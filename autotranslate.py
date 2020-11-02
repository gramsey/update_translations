# A quick-and-dirty script to run untranslated text through Google Translate's API.
# The result will likely include comical errors a native speaker will laugh at you for
# or that will puzzle them, and some manual correction of escaped codes such as @1 and @= may be
# required, but hopefully it will serve as a start to something useful

from googletrans import Translator, LANGUAGES
import os, re, shutil

pattern_tr_filename = re.compile(r'\.tr$')
pattern_tr_id = re.compile(r'\.([^.]*)\.tr$')
pattern_line_to_translate = re.compile(r'^([^#].*[^@])=$') #finds lines that don't have a translation

translator = Translator()

def translate(tr_filename):
    lang_id = pattern_tr_id.search(tr_filename)
    if not lang_id:
        print("Could not find language ID in tr filename " + tr_filename)
        return

    lang_id = lang_id.group(1)

    if not lang_id in LANGUAGES:
        print("language ID " + lang_id + " is not supported by Google Translate's API")
        return

    lines_to_translate = [] # this list of strings will ultimately be sent to Google for translation
    with open(tr_filename, "r", encoding="utf-8") as tr_file_handle:
        for line in tr_file_handle:
            # Look for lines that end in "=", ie, that don't have a valid translation added to them
            line_lacking_translation = pattern_line_to_translate.search(line)
            if line_lacking_translation:
                #break the line up at @n markers, this is not ideal for Google
                #as it may remove some context but it's necessary to allow the
                #@n markers to be preserved in the output later
                lines_to_translate = lines_to_translate + line_lacking_translation.group(1).split("@n")

        # Remove duplicates, and the empty string (a common artefact of splitting)
        line_set = set(lines_to_translate)
        line_set.discard("")
        lines_to_translate = list(line_set)

        # Only do more work if there are lines in need of translation
        if lines_to_translate:
            print("Calling Google API for " + lang_id)
            output = translator.translate(lines_to_translate, src="en", dest=lang_id)

            #convert the output translations into a dictionary for easy substitution later
            translation_dictionary = dict()
            for out_line in output:
                translation_dictionary[out_line.origin] = out_line.text

            tr_file_handle.seek(0)
            with open(tr_filename + ".temp", "w", encoding="utf-8") as tr_file_new:
                for line in tr_file_handle:
                    line_lacking_translation = pattern_line_to_translate.search(line)
                    if line_lacking_translation:
                        tr_file_new.write("#WARNING: AUTOTRANSLATED BY GOOGLE TRANSLATE\n")

                        line = line.rstrip('\n') #remove trailing newline so we can add the translated string to the same line
                        tr_file_new.write(line)
                        
                        line_split = re.split("(@n)", line[:-1]) #slice to leave off the "=" that's the last character of the line
                        #After splitting the line up on @n again, as was done before, we should have
                        #line segments that match the strings that were sent to Google.
                        for line_piece in line_split:
                            if line_piece in translation_dictionary:
                                tr_file_new.write(translation_dictionary[line_piece])
                            else:
                                #This is valid, the various @n delimiters end up here
                                tr_file_new.write(line_piece)
                        tr_file_new.write("\n")
                    else:
                        tr_file_new.write(line)
            shutil.move(tr_filename + ".temp", tr_filename) # Overwrite the original file with the new one


#If there are already .tr files in /locale, returns a list of their names
def get_existing_tr_files(folder):
    out = []
    for root, dirs, files in os.walk(folder):
        for name in files:
            if pattern_tr_filename.search(name):
                out.append(os.path.join(root,name))
    return out

tr_files = get_existing_tr_files(".")
for tr_file in tr_files:
    translate(tr_file)