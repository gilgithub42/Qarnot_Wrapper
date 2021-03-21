from os import walk
import pandas as pd
from tqdm import tqdm 

def get_files_name(path):
	f = []
	for (dirpath, _, filenames) in walk(path):
		for filename in filenames:
			if filename[-4:] == ".csv":
				f.append(dirpath + "/" + filename)
	return f


names = get_files_name("output-0dacd447-193f-4fe8-a2bf-249429b0eead/backup_dir")

end_df = None
i = 0
with tqdm(names) as tnames:
	for n in tnames:
		df = pd.read_csv(n)
		if i == 0:
			end_df = df
		else:
			end_df = end_df.append(df, ignore_index=True)
		i += 1

print(end_df)
end_df.to_csv("BestOfCartPole.csv")