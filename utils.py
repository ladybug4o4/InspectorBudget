import os
import json
from datetime import datetime


def load_config(parm=False):
    # read config data
    path = os.path.join(os.getcwd(), "my_config.json")
    if not os.path.exists(path):
        os.system('cp config.json my_config.json')
    with open(path) as config_file:
        conf = json.load(config_file)
    return conf[parm] if parm else conf


def year_month_prev(year, month, k, out=[]):
    if month - k > 0:
        out.extend([(year, m) for m in range(month, month-k, -1)])
        return out
    else:
        out.extend([(year, m) for m in range(month, 0, -1)])
        return year_month_prev(year-1, 12, k-month, out)


def year_month_next(year, month, k, out=[]):
    if month + k <= 12:
        out.extend([(year, m) for m in range(month, month+k)])
        return out
    else:
        out.extend([(year, m) for m in range(month, 13)])
        return year_month_next(year+1, 1, k - 13 + month, out)

def datename(day):
    from datepicker.datepicker import DATEFORMAT
    return datetime.strftime(datetime.strptime(day, DATEFORMAT), '%y_%m')


if __name__ == '__main__':
    print(year_month_prev(2019, 3, 6, []))
    print(year_month_next(2019, 10, 6, []))