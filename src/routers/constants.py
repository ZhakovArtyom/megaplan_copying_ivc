# constants.py

from config import settings

MEGAPLAN_API_URL = settings.MEGAPLAN_API_URL
MEGAPLAN_API_KEY = settings.MEGAPLAN_API_KEY
MEGAPLAN_HEADER = {
    "Authorization": f"Bearer {MEGAPLAN_API_KEY}",
    "Content-Type": "application/json"
}

PROGRAM_TRIGGER_DICT = {
    "7": {  # БП01.3 РЕАЛИЗАЦИЯ
        "326": "ЭнергоИнжиниринг - АльфаБанк",
        "1382": "ЭнергоИнжиниринг - Сбербанк",
        "1383": "ЭнергоИнжиниринг - Енисейский объединенный банк",
        "1380": "ЭнергоС",
        "1381": "Красэнергопроект"
    },
    "15": {  # БП12 БЫСТРАЯ ПРОДАЖА
        "847": "ЭнергоИнжиниринг - АльфаБанк",
        "1389": "ЭнергоИнжиниринг - Сбербанк",
        "1390": "ЭнергоИнжиниринг - Енисейский объединенный банк",
        "1391": "ЭнергоС",
        "1392": "Красэнергопроект"
    }
}