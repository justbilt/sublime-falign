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

	def get_line_key(self, view, line):
		key_list = []
		pos = 0
		words = []
		for v in self.align_words:
			if len(v) > 1:
				words.append('\s'+v+'\s')
			else:
				words.append(v)

		pattern = re.compile(r"({0})".format("|".join(words)))
		while True:
			match = pattern.search(line, pos)
			if not match : break
			pos = match.end()
			key_list.append({"key":match.group(),"pos":pos})

		return key_list if len(key_list) > 0 else None

	def get_line_text(self, view, index):
		return view.substr(view.line(view.text_point(index, 0)))

	def format_smiller_lines(self, main_row, row_data_dict):
		if len(row_data_dict) <= 0:
			return False, None, None, None

		main_key_list = row_data_dict[main_row]["key"]

		# find first align index
		align_index = 0
		for main_key in main_key_list:
			same = True
			for row in row_data_dict:
				try:
					row_key = row_data_dict[row]["key"][align_index]
					if row_key != main_key:
						same = False
				except IndexError:
					row_data_dict[row] = False

			if not same:
				break
			align_index += 1
		
		if align_index == len(main_key_list):
			return False, None, None, None

		align_keyword = main_key_list[align_index]["key"]
		row_region = []
		row_data = {
			main_row:{"string":row_data_dict[main_row]["string"], "pos":main_key_list[align_index]["pos"]}
		}
		for direction in [-1,1]:
			row_index = main_row + direction
			while True:
				if not row_index in row_data_dict:
					break
				data = row_data_dict[row_index]
				if data:
					row_data[row_index] = {
						"string":data["string"],
						"pos":data["key"][align_index]["pos"],
					}
				else:
					break
				row_index += direction
			row_region.append(row_index+(-direction))

		return True, row_region, align_keyword, row_data


	def get_smiller_lines(self, view, main_row):
		main_indent_level, main_string = self.get_indent_level(view, self.get_line_text(view, main_row))

		main_keys = self.get_line_key(view, main_string)
		if not main_keys:
			return False, None, None, None, None

		row_data ={
			main_row:{"string":main_string, "key":main_keys}
		}
		for direction in [-1,1]:
			row_index = main_row + direction
			while True:
				indent, string = self.get_indent_level(view, self.get_line_text(view, row_index))
				if indent != main_indent_level :
					break
				keys = self.get_line_key(view, string)
				if not keys or keys[0]["key"] != main_keys[0]["key"]:
					break
				row_data[row_index] = {"string":string, "key":keys}
				row_index += direction
		

		re, row_region, align_keyword, row_data = self.format_smiller_lines(main_row, row_data)
		if not re:
			return False, None, None, None, None

		return True, main_indent_level, align_keyword, row_region, row_data

	def align_lines(self, align_keyword, row_region, row_data):
		pos_max = 0
		for row_index in row_data:
			pos_max = max(pos_max, row_data[row_index]["pos"])

		for row_index in row_data:
			line = row_data[row_index]["string"]
			pos = row_data[row_index]["pos"]
			dis = pos_max - pos
			if dis != 0:
				row_data[row_index]["string"] = line[:pos-len(align_keyword)] + " "*(dis) + line[pos-len(align_keyword):]
			
		aligned_lines = [""]
		for row in range(row_region[0],row_region[1]):
			aligned_lines.append(row_data[row]["string"]+"\n")
		aligned_lines.append(row_data[row_region[1]]["string"])

		return aligned_lines


	def run(self, edit):
		view = self.view
		selection = view.sel()
		# get current row
		main_row = view.rowcol(view.lines(selection[0])[0].a)[0]
		
		self.align_words = [',','=',':','or']

		re,indent_level,align_keyword,row_region,row_data = self.get_smiller_lines(view, main_row)

		if not re: return

		line_list = self.align_lines(align_keyword, row_region, row_data)

		view.replace(
			edit, 
			sublime.Region(view.text_point(row_region[0],0),view.text_point(row_region[1]+1,0)-1), 
			self.get_indent_text(view, indent_level).join(line_list)
		)