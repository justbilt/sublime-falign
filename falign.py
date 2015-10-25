import sublime
import sublime_plugin
import re


class FalignCommand(sublime_plugin.TextCommand):
	def get_indent_text(self, view, indent):
		if int(view.settings().get("translate_tabs_to_spaces", False)):
			return ' '*(int(view.settings().get("tab_size", 8))*indent)
		else:
			return '\t'*indent

	def get_indent_level(self, view, line_string):
		tab_size = int(view.settings().get("tab_size", 8))
		space_count = 0
		index = 0
		for c in line_string:
			if c == " ":
				space_count += 1
			elif c == "\t":
				space_count += tab_size
			else:
				line_string = line_string[index:]
				break
			index += 1
		return int(space_count/tab_size),line_string

	def keys_equal(self, keys1, keys2):
		if len(keys1) != len(keys2):
			return False
		for i in range(len(keys1)):
			if keys1[i][0] != keys2[i][0]:
				return False
		return True

	def get_line_key(self, view, line):
		key_list = []
		pos = 0
		pattern = re.compile(r"[{0}]".format("".join(self.align_words)))
		while True:
			match = pattern.search(line, pos)
			if not match : break
			pos = match.end()
			key_list.append([match.group(),pos])

		return key_list if len(key_list) > 0 else None

	def get_line_text(self, view, index):
		return view.substr(view.line(view.text_point(index, 0)))

	def get_smiller_lines(self, view, main_row):
		main_indent_level, main_string = self.get_indent_level(view, self.get_line_text(view, main_row))

		pattern = re.compile(r"[^\w]")
		match = pattern.search(main_string)
		if not match: return False, None, None, None

		main_keys = self.get_line_key(view, main_string)
		if not main_keys: return False, None, None, None

		main_head = main_string[:match.end(0)]

		row_region =[]
		row_string ={
			str(main_row):{"string":main_string, "key":main_keys}
		}
		for direction in [-1,1]:
			index = main_row + direction
			while True:
				indent, string = self.get_indent_level(view, self.get_line_text(view, index))
				if indent != main_indent_level : break
				match = pattern.search(string)
				if not match or string[:match.end(0)] != main_head: break
				keys = self.get_line_key(view, string)
				if not keys or not self.keys_equal(main_keys, keys): break
				row_string[str(index)] = {"string":string, "key":keys}
				index += direction
			row_region.append(index+(-direction))

		if row_region[0] == row_region[1]: return False, None, None, None

		while True:
			same = True
			if len(keys) <= 0: break
			for k in row_string.values():
				if k["key"][0][0] != keys[0][0] or k["key"][0][1] != keys[0][1]:
					same = False
					break
			if same:
				for k in row_string.values():
					k["key"].pop(0)
			else:
				break
		
		if len(keys) <= 0:
			return False, None, None, None


		return True, main_indent_level, row_region, row_string

	def run(self, edit):
		view = self.view
		selection = view.sel()
		# get current row
		main_row = view.rowcol(view.lines(selection[0])[0].a)[0]
		
		self.align_words = [',','=',':']

		re,indent_level,row_region,row_string = self.get_smiller_lines(view, main_row)

		if not re: return

		keys_len = len(row_string[str(main_row)]["key"])
		for i in range(0,keys_len):
			pos_max = 0
			for key in row_string:
				pos_max = max(pos_max, row_string[key]["key"][i][1])

			for key in row_string:
				line = row_string[key]["string"]
				pos = row_string[key]["key"][i][1]
				dis = pos_max - pos
				if dis != 0:
					row_string[key]["string"] = line[:pos-1] + " "*(dis) + line[pos-1:]
					for ii in range(i, keys_len):
						row_string[key]["key"][ii][1] += dis
			break
			
		string_list = [""]
		for row in range(row_region[0],row_region[1]):
			string_list.append(row_string[str(row)]["string"]+"\n")
		string_list.append(row_string[str(row_region[1])]["string"])
		
		view.replace(
			edit, 
			sublime.Region(view.text_point(row_region[0],0),view.text_point(row_region[1]+1,0)-1), 
			self.get_indent_text(view, indent_level).join(string_list)
		)