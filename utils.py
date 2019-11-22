import os
import json


def load_config(parm=False):
    # read config data
    with open(os.path.join(os.getcwd(), "config.json")) as config_file:
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


if __name__ == '__main__':
    print(year_month_prev(2019, 3, 6, []))
    print(year_month_next(2019, 10, 6, []))
