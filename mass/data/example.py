import datasets


if __name__ == '__main__':

    ds = datasets.DSD100('/vol/vssp/datasets/audio/DSD100')
    ds = datasets.MSD100('/vol/vssp/datasets/audio/MSD100')
    ds.write()

    # Read yaml back in
    ds = datasets.Dataset.read('DSD100.yml')
    print(ds.dump())

    # Convert document to pandas DataFrame
    df = ds.to_pandas_df()
    print(df.head())
