from tinydb import TinyDB, Query
import re
import sys

db = TinyDB("db.json")

def search(title):
	Chart = Query()
	results = db.search(Chart.title.search(title, flags=re.IGNORECASE))
	if len(results) == 0:
		return 0
	elif len(results) == 1:
		return results
	elif len(results) > 1:
		return results
	else:
		return -1

def main(argv):
	title = argv[1]
	print(search(title))

if __name__ == "__main__":
	main(sys.argv)