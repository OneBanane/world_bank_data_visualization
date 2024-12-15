import world_bank_data as wb
import dask.dataframe as dd
import pandas as pd
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from html_parser import getJSONFromHTML
from db_creator import writeToMongo

class DBCreator:
    def __init__(self):
        # MongoDB конфигурация
        self.MONGO_URI = "mongodb://mongo:27017"
        self.DB_NAME = "indicators_database"
        self.COLLECTION_HEADERS = "headers"
        self.COLLECTION_MAIN_DATA = "main_data"

    async def getData(self, indicator_code: str, date="1900:2024"):
        """
        Получение данных из World Bank Data с использованием Dask.
        """
        try:
            # Загружаем данные через pandas
            res = wb.get_series(indicator_code, date=date, simplify_index=True).reset_index()

            # Конвертируем в Dask DataFrame
            res = dd.from_pandas(res, npartitions=16)

            # Фильтрация стран
            countries = wb.get_countries()
            countries = countries[countries["region"] != "Aggregates"]
            res = res[res['Country'].isin(countries['name'])]

            return res
        except Exception as e:
            raise ValueError(f"Error while fetching data for indicator '{indicator_code}': {e}")

    async def makeDB(self):
        client = AsyncIOMotorClient(self.MONGO_URI)
        db = client[self.DB_NAME]
        collection_headers = db[self.COLLECTION_HEADERS]
        collection_main_data = db[self.COLLECTION_MAIN_DATA]

        # Получение списка индикаторов
        indicators_codes = list(set([
            (d.get("name", None), d.get("indicator", None))
            async for d in collection_headers.find({}, {"indicator": 1, "name": 1})
        ]))

        # Удаляем старые данные
        await db.drop_collection(self.COLLECTION_MAIN_DATA)

        indx = 0
        tasks = []

        for name, code in indicators_codes:
            tasks.append(self.process_indicator(db, name, code, indx))
            indx += len(tasks)

        # Выполняем обработку данных параллельно
        await asyncio.gather(*tasks)

        print("Data successfully saved to MongoDB")

    async def process_indicator(self, db, name, code, indx):
        """
        Обработка одного индикатора: получение данных и запись в MongoDB с использованием Dask.
        """
        try:
            temp_data = await self.getData(code)

            # Сохраняем данные порциями
            batch_size = 1000
            temp_data["code"] = code
            temp_data["indicator_name"] = name
            temp_data = temp_data.rename(columns={code: "Y"})

            collection_main_data = db[self.COLLECTION_MAIN_DATA]
            
            # Сохранение данных порциями
            for partition in temp_data.to_delayed():  # Обработка каждой порции Dask
                batch = partition.compute()
                for i in range(0, len(batch), batch_size):
                    chunk = batch.iloc[i:i + batch_size].to_dict(orient="records")
                    await collection_main_data.insert_many(chunk)

        except Exception as e:
           print(f"Error processing indicator {code}: {e}")

COLLECTION_HEADERS = "headers"
COLLECTION_MAIN_DATA = "main_data"

path_in = "./data/indicators_data.html"
path_out = "./data/indicators.json" 
indicators_json = getJSONFromHTML(path_in, path_out, save=True)
writeToMongo(indicators_json["indicators"], collection_name=COLLECTION_HEADERS)

creator = DBCreator()
asyncio.run(creator.makeDB())
