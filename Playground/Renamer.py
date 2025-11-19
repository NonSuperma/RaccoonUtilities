from Raccoon.windowsUtilities import *
import re


def capitalize(name: str) -> str:
	wordList = name.split(' ')
	wordList_capitalized = []
	for word in wordList:
		wordList_capitalized.append(word.capitalize())
	return str.join(' ', wordList_capitalized)


def dotIndex(name: str) -> str:
	for i, char in enumerate(name):
		if not char.isdigit():
			if char == '.':
				return name
			if i == 0:
				return name
			return name[:i] + '.' + name[i:]
	return name


def removeBetween(name: str, start_char: str, end_char: str) -> str:
	return name[:start_char] + name[end_char:]


def main():
	tempInput = input('d - dics\n'
					  'f - files\n')
	if tempInput == 'd':
		winDirPath()
	filePaths = winFilesPath()
	fileCount = len(filePaths)

	fileNames = []
	for path in filePaths:
		fileNames.append(path.name)

	#  Print the intial file list
	for index in range(fileCount):
		print(f'{index+1}. ---  "{fileNames[index]}"')

	print(f'\n  Replacing')
	turn = 0
	tempReplacedList = fileNames
	while True:
		symbol_toReplace = input('what to replace?   ("enter" x2 to stop)\n: ')
		symbol_replaced = input('what to replace WITH?\n: ')
		if symbol_toReplace == symbol_replaced:
			break

		for index in range(fileCount):
			tempReplacedList[index] = tempReplacedList[index].replace(symbol_toReplace, symbol_replaced)

		if turn != 0:
			for i in range(len(tempReplacedList)+4):
				sys.stdout.write("\033[F\033[K")

		for index in range(fileCount):
			print(f'{index+1}. ---  "{tempReplacedList[index]}"')

		turn += 1
	replacedList = tempReplacedList

	print(f'\n  Functions\n'
		  f'capitalize - c - capitalize each word in each name\n'
		  f'dotIndex - d - add a dot at the end of index 00. \n'
		  f'removeBetween - r - remove a character between two characters\n')

	turn = 0
	tempList = replacedList

	while True:
		userInput = input('Option\n: ')
		if userInput == '':
			replacedList = tempList
			break
		if turn != 0:
			for i in range(len(tempList)+4):
				sys.stdout.write("\033[F\033[K")

		if userInput == 'c':
			for index in range(fileCount):
				tempList[index] = capitalize(tempList[index])
			for index in range(fileCount):
				print(f'{index+1}. ---  "{tempList[index]}"')

		elif userInput == 'd':
			for index in range(fileCount):
				tempList[index] = dotIndex(tempList[index])
			for index in range(fileCount):
				print(f'{index + 1}. ---  "{tempList[index]}"')

		elif userInput == 'r':
			start_char = input('start character ("enter" to begin from start)\n: ')
			end_char = input('end character ("enter" to stop at the end)\n: ')

			for index in range(fileCount):
				if start_char == '':
					start_char = 0
				if end_char == '':
					end_char = len(fileCount[index])
				tempList[index] = removeBetween(tempList[index], start_char, end_char)

		turn += 1

	print('\n\nFinal list:\n')
	for index in range(fileCount):
		print(f'{index+1}. ---  "{replacedList[index]}"')

	for index in range(fileCount):
		filePaths[index].rename(filePaths[index].parent / replacedList[index])


if __name__ == '__main__':
	main()
