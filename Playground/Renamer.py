from Raccoon.windowsUtilities import *
import re


def capitalize(string: str) -> str:
	wordList = string.split(' ')
	wordList_capitalized = []
	for word in wordList:
		wordList_capitalized.append(word.capitalize())
	return str.join(' ', wordList_capitalized)


def dot_indexes(string: str) -> str:
	for i, char in enumerate(string):
		if not char.isdigit():
			if char == '.':
				return string
			if i == 0:
				return string
			return string[:i] + '.' + string[i:]
	return string


def remove_between(string: str, start_char: str, end_char: str) -> str:
	return string[:string.find(start_char)] + string[string.find(end_char)+1:]


def main():
	tempInput = input('d - dics\n'
					  'f - files\n'
					  ': ')

	if tempInput.lower() == 'd':
		dir_paths = win_dirs_path('Select directories you want renamed')

		if not dir_paths:
			raise ValueError('No directories selected.')

		dir_names = []
		for dir in dir_paths:
			dir_names.append(dir.name)

		dir_count = len(dir_names)

		#  Print the intial dir list
		for index in range(dir_count):
			print(f'{index + 1}. ---  "{dir_names[index]}"')

		print(f'\n  Replacing')
		turn = 0
		temp_replaced_list = dir_names
		while True:
			symbol_toReplace = input('what to replace?   ("enter" x2 to stop)\n: ')
			symbol_replaced = input('what to replace WITH?\n: ')
			if symbol_toReplace == symbol_replaced:
				break

			for index in range(dir_count):
				temp_replaced_list[index] = temp_replaced_list[index].replace(symbol_toReplace, symbol_replaced)

			if turn != 0:
				for i in range(len(temp_replaced_list) + 4):
					sys.stdout.write("\033[F\033[K")

			for index in range(dir_count):
				print(f'{index + 1}. ---  "{temp_replaced_list[index]}"')

			turn += 1
		replaced_list = temp_replaced_list

		print(f'\n  Functions\n'
			  f'capitalize - c - capitalize each word in each name\n'
			  f'dotIndex - d - add a dot at the end of index 00. \n'
			  f'removeBetween - r - remove a character between two characters\n')

		turn = 0
		tempList = replaced_list

		while True:
			userInput = input('Option\n: ')
			if userInput == '':
				replaced_list = tempList
				break
			if turn != 0:
				for i in range(len(tempList) + 4):
					sys.stdout.write("\033[F\033[K")

			if userInput == 'c':
				for index in range(dir_count):
					tempList[index] = capitalize(tempList[index])
				for index in range(dir_count):
					print(f'{index + 1}. ---  "{tempList[index]}"')

			elif userInput == 'd':
				for index in range(dir_count):
					tempList[index] = dot_indexes(tempList[index])
				for index in range(dir_count):
					print(f'{index + 1}. ---  "{tempList[index]}"')

			elif userInput == 'r':
				start_char = input('start character ("enter" to begin from start)\n: ')
				end_char = input('end character ("enter" to stop at the end)\n: ')

				for index in range(dir_count):
					if start_char == '':
						start_char = 0
					if end_char == '':
						end_char = len(dir_count[index])
					tempList[index] = remove_between(tempList[index], start_char, end_char)

			turn += 1

		print('\n\nFinal list:\n')
		for index in range(dir_count):
			print(f'{index + 1}. ---  "{replaced_list[index]}"')

		for index in range(dir_count):
			file_paths[index].rename(file_paths[index].parent / replaced_list[index])

	elif tempInput.lower() == 'f':
		file_paths = win_files_path('Select files you want renamed')

	names = []
	for file_path in file_paths:
		names.append(file_path.name)

	count = len(names)

	#  Print the intial file list
	for index in range(count):
		print(f'{index+1}. ---  "{names[index]}"')

	print(f'\n  Replacing')
	turn = 0
	temp_replaced_list = names
	while True:
		symbol_toReplace = input('what to replace?   ("enter" x2 to stop)\n: ')
		symbol_replaced = input('what to replace WITH?\n: ')
		if symbol_toReplace == symbol_replaced:
			break

		for index in range(count):
			temp_replaced_list[index] = temp_replaced_list[index].replace(symbol_toReplace, symbol_replaced)

		if turn != 0:
			for i in range(len(temp_replaced_list)+4):
				sys.stdout.write("\033[F\033[K")

		for index in range(count):
			print(f'{index+1}. ---  "{temp_replaced_list[index]}"')

		turn += 1
	replaced_list = temp_replaced_list

	print(f'\n  Functions\n'
		  f'capitalize - c - capitalize each word in each name\n'
		  f'dotIndex - d - add a dot at the end of index 00. \n'
		  f'removeBetween - r - remove a character between two characters\n')

	turn = 0
	tempList = replaced_list

	while True:
		userInput = input('Option\n: ')
		if userInput == '':
			replaced_list = tempList
			break
		if turn != 0:
			for i in range(len(tempList)+4):
				sys.stdout.write("\033[F\033[K")

		if userInput == 'c':
			for index in range(count):
				tempList[index] = capitalize(tempList[index])
			for index in range(count):
				print(f'{index+1}. ---  "{tempList[index]}"')

		elif userInput == 'd':
			for index in range(count):
				tempList[index] = dot_indexes(tempList[index])
			for index in range(count):
				print(f'{index + 1}. ---  "{tempList[index]}"')

		elif userInput == 'r':
			start_char = input('start character ("enter" to begin from start)\n: ')
			end_char = input('end character ("enter" to stop at the end)\n: ')

			for index in range(count):
				if start_char == '':
					start_char = 0
				if end_char == '':
					end_char = len(count[index])
				tempList[index] = remove_between(tempList[index], start_char, end_char)

		turn += 1

	print('\n\nFinal list:\n')
	for index in range(count):
		print(f'{index+1}. ---  "{replaced_list[index]}"')

	for index in range(count):
		file_paths[index].rename(file_paths[index].parent / replaced_list[index])


if __name__ == '__main__':
	main()
