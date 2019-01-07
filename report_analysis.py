import pandas as pd


def file_reader(log_file_name):
    records = list()
    record = dict()
    with open(log_file_name, 'r') as file:
        while True:
            line = file.readline()
            if len(line) == 0:
                break
            line = line.replace('\n', '')
            if len(line) < 1:
                if record not in records:
                    records.append(record)
                continue
            colname, value = line.split(':')
            if colname == 'model_form':
                record = dict()
            record[colname] = value
    return records





if __name__ == '__main__':
    log_file_name = 'log/backtesting_result.txt'
    data_dict = file_reader(log_file_name)
    df = pd.DataFrame(data_dict)
    print(df.sort_values('calmar_ratio', ascending=False))