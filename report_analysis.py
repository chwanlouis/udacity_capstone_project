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
    log_file_name = 'log/walk_forward_backtesting_result_sec_3.txt'
    data_dict = file_reader(log_file_name)
    df = pd.DataFrame(data_dict)
    selected_df = df.sort_values('cumulative_returns', ascending=False)[0:10]
    # selected_df.to_csv('walk_forward_backtest_summary.csv', index=False)
    print(selected_df)
    # print(df[df['model_form'] == 'benchmark'])