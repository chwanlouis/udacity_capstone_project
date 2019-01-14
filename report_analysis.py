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
    records = list()
    benchmark_c_returns = None
    for num in range(2, 25):
        log_file_name = 'log/walk_forward_backtesting_result_sec_%s.txt' % num
        print('Reading file: %s' % log_file_name)
        data_dict = file_reader(log_file_name)
        df = pd.DataFrame(data_dict)
        if benchmark_c_returns is None:
            benchmark_c_returns = df[df['model_form'] == 'benchmark']['cumulative_returns'].values.tolist()[0]
        selected_df = df[df['cumulative_returns'] > benchmark_c_returns]
        n_records = len(selected_df)
        if n_records > 0:
            print('%s found' % n_records)
            selected_records = selected_df.to_dict('records')
            for record in selected_records:
                record['walk_forward_steps'] = num
                records.append(record)
    output_df = pd.DataFrame(records)
    output_df.to_csv('walk_forward_report.csv', index=False)

    # print(df[df['model_form'] == 'benchmark'])