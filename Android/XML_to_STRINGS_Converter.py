import msvcrt
import time
import re
import os

try:
    from lxml import etree as ET
except ImportError:
    import subprocess
    import sys
    print("Module 'lxml' not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lxml"])
    from lxml import etree as ET

APP_NAME = os.path.basename(__file__).replace("_", " ").strip(".py")

class InvalidFileFormat(BaseException): ...

def is_valid_windows_filename(name):
    invalid_chars = set('<>:"/\\|?*')
    if any(char in name for char in invalid_chars):
        return False
    if name.endswith(' ') or name.endswith('.'):
        return False
    base = os.path.splitext(name)[0].upper()
    reserved_windows_names = [
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    ]
    if base in reserved_windows_names:
        return False
    return True

def print_box(lines:list[str], h_padd:int = 4, v_padd:int = 2, alignment:str = "left"):
    """_summary_

    Args:
        lines (list[str]): list of strings to be printed.
        h_padd (int, optional): Horizontal Padding. Defaults to 4.
        v_padd (int, optional): Vertical Padding. Defaults to 2.
        alignment (str, optional): Alignment of lines. Avaliable options are left, right and center.
    """
    max_length = max(len(line) for line in lines)
    
    half_h_padd = " " * int(h_padd/2)
    half_v_padd = int(v_padd/2)

    top_border = "┌" + "─" * (max_length + h_padd) + "┐"
    bottom_border = "└" + "─" * (max_length + h_padd) + "┘"

    print(top_border)
    for _ in range(0, half_v_padd):
        print(f"│{" " * (max_length + h_padd)}│")
    
    for line in lines:
        line = (line.ljust(max_length) if alignment == "left" else line.rjust(max_length) if alignment == "right" else line.center(max_length))
        print(f"│{half_h_padd}{line}{half_h_padd}│")
    
    for _ in range(0, half_v_padd):
        print(f"│{" " * (max_length + h_padd)}│")
    print(bottom_border)

def quote_unicode(s: str):
    if not s:
        return s
    
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    
    # s = s.replace("\\", "\\\\")  # Backslash must be first
    # s = s.replace("\"", "\\\"")  # Double quote
    # s = s.replace("\'", "\\'")   # Single quote
    s = s.replace("\a", "\\a")   # Bell
    s = s.replace("\b", "\\b")   # Backspace
    s = s.replace("\f", "\\f")   # Form feed
    s = s.replace("\n", "\\n")   # Newline
    s = s.replace("\r", "\\r")   # Carriage return
    s = s.replace("\t", "\\t")   # Tab
    s = s.replace("\v", "\\v")   # Vertical tab
    s = s.replace("\0", "\\0")   # Null character
    
    return s

def unquote_unicode(s: str):
    if not s:
        return s
    
    s = s.replace("\\a", "\a")
    s = s.replace("\\b", "\b")
    s = s.replace("\\f", "\f")
    s = s.replace("\\n", "\n")
    s = s.replace("\\r", "\r")
    s = s.replace("\\t", "\t")
    s = s.replace("\\v", "\v")
    s = s.replace("\\0", "\0")
    # s = s.replace("\\\"", "\"")
    # s = s.replace("\\'", "'")
    # s = s.replace("\\\\", "\\")
    
    if "  " in s or "'" in s or "\n" in s or "\r" in s or "\t" in s or s[0] == " " or s[-1] == " ":
        s = f'"{s}"'
        
    if s[0] == "?":
        s = f"\\{s}"
    
    return s

def choice_input(msg:str, options:list[int]):
    try:
        choice = int(input(msg))
        if choice not in options:
            raise ValueError
        return choice
    except ValueError:
        print("Invalid choice! Try again."); time.sleep(1); choice_input(msg, options)

def file_input(kind: str, extension: str, default: str = ""):
    try:
        extension = f".{extension.lower()}"
        file_path = ""

        if kind == "new":
            file_path = input(f"Enter a name of {extension} output file" + (f" (default: {default}): " if default else ": ")).strip()

            if not file_path and default:
                file_path = default

            file_path = file_path + extension

            if not is_valid_windows_filename(os.path.basename(file_path)):
                raise InvalidFileFormat("Filename contains invalid characters, ends with space/dot, or uses a reserved name.")

            print()

            while os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                choice = choice_input(f"File '{file_name}' already exists! Would you like to overwrite the file?\n1. Yes\n2. No\n>>> ", [1, 2])
                if choice == 1:
                    break
                else:
                    match = re.match(r'^(.*?)(?: \((\d+)\))?(\.\w+)$', file_path)
                    if match:
                        name = match.group(1)
                        count = int(match.group(2)) + 1 if match.group(2) else 1
                        ext = match.group(3)
                        file_path = f"{name} ({count}){ext}"
                    else:
                        name, ext = os.path.splitext(file_path)
                        file_path = f"{name} (1){ext}"

        elif kind == "existing":
            file_path = input(f"Enter the path to a {extension} file: ").strip().strip('"')

            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"Specified {extension} file not found! Try again.")
            elif not file_path.lower().endswith(extension):
                raise InvalidFileFormat(f"Invalid file format! Should be {extension}!")

        return file_path

    except (FileNotFoundError, InvalidFileFormat) as e:
        print(str(e))
        time.sleep(1)
        return file_input(kind, extension.strip("."), default)

def get_xml_strings(file_path: str):
    tree = ET.parse(file_path, parser=None)
    root = tree.getroot()
    strings = {}

    for child in root.iter("string"):
        name = child.get("name")
        if name:
            text = child.text
            strings[name] = text

    return strings

def export_strings(file_path: str, strings: dict):
    try:
        exported_strings_count = 0
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"/* Generated by veydzh3r's {APP_NAME} */\n")
            for name in sorted(strings):
                if strings[name] is not None:
                    text = quote_unicode(strings[name])
                    f.write(f"\"{name}\" = \"{text}\";\n")
                    exported_strings_count += 1
                else:
                    f.write(f"\"{name}\" = \"\";\n")
    except Exception as e:
        print(f"Export error: {str(e)}")
        return False
    
    file_path = os.path.basename(file_path)
    print_box([
        f"Total strings: {len(strings)}",
        f"Exported strings: {exported_strings_count}",
        f"Strings have been written to {file_path} file!"
    ])
    return True

def get_apple_strings(file_path: str):
    try:
        try:
            with open(file_path, "r", encoding="utf-16") as f:
                content = f.read()
        except UnicodeError:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}

    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'//.*', '', content)

    pattern = r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;'
    matches = re.findall(pattern, content, flags=re.DOTALL)

    result = {}
    for key, value in matches:
        unescaped_key = unquote_unicode(key)
        unescaped_value = unquote_unicode(value)
        result[unescaped_key] = unescaped_value

    return result

def import_strings(source_file: str, output_file: str, strings: dict):
    try:
        tree = ET.parse(source_file, parser=None)
        root = tree.getroot()
        import_strings_count = 0
        
        for str_obj in root.iter("string"):
            obj_name = str_obj.get("name")
            if obj_name in strings and obj_name:
                old_text = str_obj.text
                new_text = strings[obj_name]
                if old_text != new_text and old_text is not None:
                    print(f"Changed: {obj_name}")
                    print(f"  From: {repr(old_text)}")
                    print(f"  To:   {repr(new_text)}")
                    str_obj.text = new_text
                    import_strings_count += 1

        if import_strings_count != 0:
            tree.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)
            output_file = os.path.basename(output_file)
            print_box([
                f"Total strings: {len(root.xpath('.//string'))}",
                f"Imported strings: {import_strings_count}",
                f"Strings have been imported to {output_file}!"
            ])
        else:
            print("Found no strings to update!")
    
    except Exception as e:
        print(f"Import error: {e}")

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print_box(["XML to STRINGS Converter Program by veydzh3r", "Github: https://github.com/Veydzher/Translation-Tools"], 6, 2, "center")
    try:
        choice = choice_input("1. Export strings from .xml\n2. Import strings from .strings\n3. Exit the program\n\n>>> ", [1,2,3])
        
        if choice == 1:
            xml_file_path = file_input("existing", "xml")
        
            output_file = file_input("new", "strings", "Localizable")
                
            print()
                
            strings = get_xml_strings(xml_file_path)
            if strings:
                export_strings(output_file, strings)
            else:
                print("No strings found in XML file!")
                
        elif choice == 2:
            xml_file_path = file_input("existing", "xml")
        
            apple_file_path = file_input("existing", "strings")
            
            output_file = file_input("new", "xml", "strings_edited")
                
            print()
            
            modified_strings = get_apple_strings(apple_file_path)
            if modified_strings:
                import_strings(xml_file_path, output_file, modified_strings)
            else:
                print("No valid strings found in .strings file!")
        
        elif choice == 3:
            print("Exiting the program...")
            exit(0)
        
        print("\nPress any key to exit main menu..."); msvcrt.getch(); main()
    
    except FileNotFoundError as e:
        print(str(e)); time.sleep(1); clear(); main()
    except InvalidFileFormat as e:
        print(str(e)); time.sleep(1); clear(); main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user."); exit(0)
    except Exception as e:
        print(f"Unexpected error: {str(e)}\nReport the error to veydzh3r."); print("\nPress any key to exit..."); msvcrt.getch(); exit(0)

if __name__ == "__main__":
    main()
