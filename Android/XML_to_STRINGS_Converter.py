import re
import os
import time
import json
import msvcrt
import logging
import platform
from pathlib import Path

try:
    from lxml import etree as ET # type: ignore
except ImportError:
    import subprocess
    import sys
    print("Module 'lxml' not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lxml"])
    from lxml import etree as ET # type: ignore

class InvalidFileExtension(BaseException): ...
class UserCancelled(BaseException): ...

APP_NAME = "Android XML to iOS STRINGS Converter"

class XMLtoSTRINGS:
    def __init__(self):
        self.ts = {
            "app_title": f"{APP_NAME} by veydzh3r",
            "menu_option_1": "Export strings from .xml",
            "menu_option_2": "Import strings from .strings",
            "menu_option_3": "Settings",
            "menu_option_4": "Exit",
            "file_input_default": " (default: {}): ",
            "file_input_new": "Enter a name for {} output file",
            "file_input_new_invalid": "Filename contains invalid characters, ends with space/dot, or uses a reserved OS name.",
            "file_input_existing": "Enter the path to a {} file: ",
            "file_input_existing_not_found": "Specified {} file not found! Try again.",
            "file_input_existing_invalid": "Invalid file format! Should be {}!",
            "menu_option_1_result": "No strings found in .xml file!",
            "menu_option_2_result": "No strings found in .strings file!",
            "menu_option_4_result": "Exiting the program...",
            "settings_title": "Settings",
            "settings_option_1": "Toggle detailed export output: {}",
            "settings_option_2": "Toggle detailed import output: {}",
            "settings_option_3": "Back",
            "export_error": "Export error: {}",
            "total_strings": "Total strings: {}",
            "exported_strings": "Exported strings: {}",
            "exported_empty_strings": "Exported empty strings: {}",
            "skipped_empty_strings": "Skipped empty strings: {}",
            "strings_saved": "Strings have been saved to {}!",
            "strings_reading_error": "Error reading file {}: {}",
            "imported_strings": "Imported strings: {}",
            "no_strings_to_update": "Found no strings to update!",
            "import_error": "Import error: {}",
            "press_any_key_to_exit": "Press any key to exit...",
            "program_interrupted": "Program interrupted by user.",
            "unexpected_error": "Unexpected error: {}\nReport the error to veydzh3r."
        }
        self.config = Config()
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Application started: {APP_NAME}")
        self.main()
    
    def setup_logging(self):
        log_file = "xml_to_strings.log"
        log_dir = Path(self.config.get_config_path(log_file, f"veydzh3r\\{APP_NAME}"))
        
        log_level = getattr(logging, self.config.get("log_level", "INFO").upper()) # type: ignore
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_dir,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        
        logging.basicConfig(
            level=log_level,
            handlers=[file_handler, console_handler]
        )
        
    def main(self):
        while True:
            try:
                self.clear()
                self.print_box([self.ts["app_title"], "Github: https://github.com/Veydzher/Translation-Tools"], 6, 2, "center")
                choice = self.choice_input("", {1: self.ts["menu_option_1"], 2: self.ts["menu_option_2"], 3: self.ts["menu_option_3"], 4: self.ts["menu_option_4"]})
                
                self.logger.info(f"User selected menu option: {choice}")
                
                if choice == 1:
                    self.logger.info("Starting XML to STRINGS export process")
                    xml_file_path = self.file_input("existing", "xml")
                    
                    if xml_file_path:
                        self.logger.info(f"XML file selected: {xml_file_path}")
                        output_file = self.file_input("new", "strings", "Localizable")
                        
                        if output_file:
                            self.logger.info(f"Output file selected: {output_file}")
                            print()
                            
                            strings = self.get_xml_strings(xml_file_path)
                            if strings:
                                self.export_strings(output_file, strings)
                            else:
                                self.logger.warning(f"No strings found in XML file: {xml_file_path}")
                                print(self.ts["menu_option_1_result"])
                
                elif choice == 2:
                    self.logger.info("Starting STRINGS to XML import process")
                    xml_file_path = self.file_input("existing", "xml")
                    
                    if xml_file_path:
                        self.logger.info(f"Source XML file selected: {xml_file_path}")
                        apple_file_path = self.file_input("existing", "strings")
                        
                        if apple_file_path:
                            self.logger.info(f"STRINGS file selected: {apple_file_path}")
                            output_file = self.file_input("new", "xml", "strings_edited")
                            
                            if output_file:
                                self.logger.info(f"Output XML file selected: {output_file}")
                                print()
                                
                                modified_strings = self.get_apple_strings(apple_file_path)
                                if modified_strings:
                                    self.import_strings(xml_file_path, output_file, modified_strings)
                                else:
                                    self.logger.warning(f"No strings found in STRINGS file: {apple_file_path}")
                                    print(self.ts["menu_option_2_result"])
                
                elif choice == 3:
                    self.logger.info("Opening settings menu")
                    self.open_settings()
                
                elif choice == 4:
                    self.logger.info("User requested exit")
                    print(self.ts["menu_option_4_result"])
                    exit(0)
                
                else:
                    self.logger.warning(f"Invalid menu choice: {choice}")
                    break
                
                print(f"\n{self.ts['press_any_key_to_exit']}"); msvcrt.getch(); self.main()
            
            except FileNotFoundError as e:
                self.logger.error(f"File not found: {str(e)}")
                print(str(e)); time.sleep(1); self.clear(); continue
            except InvalidFileExtension as e:
                self.logger.error(f"Invalid file extension: {str(e)}")
                print(str(e)); time.sleep(1); self.clear(); continue
            except KeyboardInterrupt:
                self.logger.info("Program interrupted by user (Ctrl+C)")
                print(f"\n\n{self.ts['program_interrupted']}"); exit(0)
            except UserCancelled:
                self.logger.info("Operation cancelled by user (ESC)")
                continue
            except Exception as e:
                self.logger.exception(f"Unexpected error in main loop: {str(e)}")
                print(f"{self.ts['unexpected_error'].format(str(e))}\n{self.ts['press_any_key_to_exit']}")
                msvcrt.getch()
                break
            
    def open_settings(self):
        detailed_export = self.config.get("detailed_export")
        detailed_import = self.config.get("detailed_import")
        
        self.clear()
        self.print_box([APP_NAME, self.ts["settings_title"]], alignment="center")
        choice = self.choice_input("", {1: self.ts["settings_option_1"].format(detailed_export), 2: self.ts["settings_option_2"].format(detailed_import), 3: self.ts["settings_option_3"]})

        if choice == 1:
            new_value = not detailed_export
            self.config.set("detailed_export", new_value)
            self.logger.info(f"Changed detailed_export setting to: {new_value}")
        elif choice == 2:
            new_value = not detailed_import
            self.config.set("detailed_import", new_value)
            self.logger.info(f"Changed detailed_import setting to: {new_value}")
        elif choice == 3:
            self.logger.info("Returning to main menu from settings")
            return
        
        self.open_settings()
    
    def get_xml_strings(self, file_path: str):
        self.logger.info(f"Parsing XML file: {file_path}")
        try:
            tree = ET.parse(file_path, parser=None)
            root = tree.getroot()
            strings = {}
            
            for child in root.iter("string"):
                name = child.get("name")
                if name:
                    text = child.text
                    strings[name] = text
                    self.logger.debug(f"Found string: {name} = {text}")
            
            self.logger.info(f"Successfully parsed {len(strings)} strings from XML file")
            return strings
            
        except ET.XMLSyntaxError as e:
            self.logger.error(f"XML syntax error in file {file_path}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing XML file {file_path}: {str(e)}")
            raise
    
    def export_strings(self, file_path: str, strings: dict, export_none_strings: bool = False):
        self.logger.info(f"Exporting {len(strings)} strings to: {file_path}")
        try:
            exported_strings_count = 0
            exported_none_strings_count = 0
            skipped_none_strings_count = 0
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"/* Generated by veydzh3r's {APP_NAME}: https://github.com/Veydzher/Translation-Tools/tree/main/Android */\n")
                for name in sorted(strings):
                    if strings[name] is not None:
                        text = self.quote_unicode(strings[name])
                        f.write(f"\"{name}\" = \"{text}\";\n")
                        exported_strings_count += 1
                        self.logger.debug(f"Exported string: {name}")
                    else:
                        if export_none_strings:
                            f.write(f"\"{name}\" = \"\";\n")
                            exported_none_strings_count += 1
                            self.logger.debug(f"Exported empty string: {name}")
                        else:
                            skipped_none_strings_count += 1
                            self.logger.debug(f"Skipped empty string: {name}")
            
            self.logger.info(f"Export completed: {exported_strings_count} strings exported, {skipped_none_strings_count} empty strings skipped")
            
        except Exception as e:
            self.logger.error(f"Export error for file {file_path}: {str(e)}")
            print(self.ts["export_error"].format(str(e)))
            return False
        
        filename = os.path.basename(file_path)
        detailed_export = self.config.get("detailed_export")
        
        if detailed_export:
            self.print_box([
                self.ts["total_strings"].format(len(strings)),
                self.ts["exported_strings"].format(exported_strings_count),
                self.ts["exported_empty_strings"].format(exported_none_strings_count) if exported_none_strings_count else self.ts["skipped_empty_strings"].format(skipped_none_strings_count),
                self.ts["strings_saved"].format(filename)
            ])
        else:
            self.print_box([
                self.ts["total_strings"].format(len(strings)),
                self.ts["exported_strings"].format(exported_strings_count),
                self.ts["strings_saved"].format(filename)
            ])
        
        return True
    
    def get_apple_strings(self, file_path: str):
        self.logger.info(f"Parsing STRINGS file: {file_path}")
        try:
            content = None
            encoding_used = None
            
            for encoding in ["utf-16", "utf-8"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                        encoding_used = encoding
                        break
                except UnicodeError:
                    continue
            
            if content is None:
                raise Exception("Could not decode file with utf-16 or utf-8 encoding")
            
            self.logger.info(f"Successfully read file using {encoding_used} encoding")
            
        except Exception as e:
            self.logger.error(f"Error reading STRINGS file {file_path}: {str(e)}")
            print(self.ts["strings_reading_error"].format(file_path, str(e)))
            return {}
        
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'//.*', '', content)
        
        pattern = r'"(.*?)"\s*=\s*"(.*?)"\s*;'
        matches = re.findall(pattern, content, flags=re.DOTALL)
        
        result = {}
        for key, value in matches:
            unescaped_key = self.unquote_unicode(key)
            unescaped_value = self.unquote_unicode(value)
            result[unescaped_key] = unescaped_value
            self.logger.debug(f"Parsed string: {unescaped_key} = {unescaped_value}")
        
        self.logger.info(f"Successfully parsed {len(result)} strings from STRINGS file")
        return result
    
    def import_strings(self, source_file: str, output_file: str, strings: dict):
        self.logger.info(f"Importing strings from {source_file} to {output_file}")
        try:
            tree = ET.parse(source_file, parser=None)
            root = tree.getroot()
            
            import_strings_count = 0
            success_import_strings = []
            failed_import_strings = []
            
            for str_obj in root.iter("string"):
                obj_name = str_obj.get("name")
                if obj_name in strings and obj_name:
                    old_text = str_obj.text
                    new_text = strings[obj_name]
                    if old_text != new_text and old_text is not None:
                        success_import_strings.append(f"\tKey: \"{obj_name}\"\n\tOld: {old_text}\n\tNew: {new_text}\n")
                        str_obj.text = new_text
                        import_strings_count += 1
                        self.logger.debug(f"Updated string '{obj_name}': '{old_text}' -> '{new_text}'")
                    else:
                        failed_import_strings.append(f"\tKey: \"{obj_name}\"\n\tOld: {old_text}\n\tNew: {new_text}\n")
                        self.logger.debug(f"No change for string '{obj_name}': '{old_text}'")
            
            self.logger.info(f"Import process completed: {import_strings_count} strings updated")
            
            detailed_import = self.config.get("detailed_import")
            
            if detailed_import:
                if success_import_strings:
                    success_file = "success_import_strings.txt"
                    with open(success_file, "w+", encoding="utf-8") as sf:
                        sf.write("Successfully imported the following strings:\n")
                        for ses in success_import_strings:
                            sf.write(f"{ses}\n")
                    self.logger.info(f"Detailed success log written to: {success_file}")
                
                if failed_import_strings:
                    failed_file = "failed_import_strings.txt"
                    with open(failed_file, "w+", encoding="utf-8") as ff:
                        ff.write("Failed to import the following strings:\n")
                        for fis in failed_import_strings:
                            ff.write(f"{fis}\n")
                    self.logger.info(f"Detailed failure log written to: {failed_file}")
            
            if import_strings_count != 0:
                tree.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)
                output_filename = os.path.basename(output_file)
                self.logger.info(f"Updated XML file saved as: {output_file}")
                self.print_box([
                    self.ts["total_strings"].format(len(root.xpath('.//string'))),
                    self.ts["imported_strings"].format(import_strings_count),
                    self.ts["strings_saved"].format(output_filename)
                ])
            else:
                self.logger.warning("No strings were updated during import")
                print(self.ts["no_strings_to_update"])
        
        except Exception as e:
            self.logger.error(f"Import error: {str(e)}")
            print(self.ts["import_error"].format(str(e)))
    
    def choice_input(self, msg: str, options: dict[int, str]):
        try:
            if msg:
                print(msg)
            
            for num, string in options.items():
                print(f"{num}. {string}")
            
            choice = int(input(">>> "))
            if choice not in options.keys():
                raise ValueError
            return choice
        except ValueError:
            self.logger.warning(f"Invalid menu choice entered")
            return None
    
    def getch(self):
        try:
            # Windows
            return msvcrt.getwch()
        except ImportError:
            # Unix (Linux/macOS)
            import sys, tty, termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd) # type: ignore
            try:
                tty.setraw(fd) # type: ignore
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings) # type: ignore
            return ch
    
    def file_input(self, kind: str, extension: str, default: str = ""):
        def esc_input(prompt: str):
            print(prompt, end="", flush=True)
            buffer = ""
            while True:
                ch = self.getch()
                if ch == '\r':  # Enter
                    print()
                    return buffer.strip().strip('"') if buffer else ""
                elif ch == '\x1b':  # ESC
                    return None
                elif ch == '\b':  # Backspace
                    if buffer:
                        buffer = buffer[:-1]
                        print("\b \b", end="", flush=True)
                else:
                    buffer += ch
                    print(ch, end="", flush=True)
        
        try:
            file_path = ""
            display_ext = f".{extension.lower()}"

            if kind == "new":
                file_path = esc_input(self.ts["file_input_new"].format(display_ext) + (self.ts["file_input_default"].format(default) if default else ": "))
                
                if file_path is None:
                    self.logger.info("User cancelled file input (ESC pressed)")
                    raise UserCancelled
                
                if not file_path and default:
                    file_path = default
                
                file_path = file_path + display_ext
                
                if not self.is_valid_windows_filename(os.path.basename(file_path)):
                    self.logger.warning(f"Invalid filename provided: {file_path}")
                    raise InvalidFileExtension(self.ts["file_input_new_invalid"])
                
                original_path = file_path
                counter = 1
                while os.path.exists(file_path):
                    file = os.path.basename(original_path)
                    name, ext = os.path.splitext(file)
                    file_path = f"{name} - Copy{f' ({counter})' if counter > 1 else ''}{ext}"
                    counter += 1
                    
                if file_path != original_path:
                    self.logger.info(f"File exists, using alternate name: {file_path}")
            
            elif kind == "existing":
                file_path = esc_input(self.ts["file_input_existing"].format(display_ext))
                
                if file_path is None:
                    self.logger.info("User cancelled file input (ESC pressed)")
                    raise UserCancelled
                    
                if not os.path.exists(file_path):
                    self.logger.warning(f"File not found: {file_path}")
                    raise FileNotFoundError(self.ts["file_input_existing_not_found"].format(display_ext))
                    
                elif not file_path.lower().endswith(display_ext):
                    self.logger.warning(f"Invalid file extension for: {file_path}, expected: {display_ext}")
                    raise InvalidFileExtension(self.ts["file_input_existing_invalid"].format(display_ext))

            return file_path
        
        except (FileNotFoundError, InvalidFileExtension) as e:
            print(str(e))
            time.sleep(1)
            return self.file_input(kind, extension, default)
        except UserCancelled:
            raise
    
    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def is_valid_windows_filename(self, name):
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

    def print_box(self, lines: list[str], h_padd: int = 4, v_padd: int = 2, alignment: str = "left"):
        """
        Args:
            lines (list[str]): list of strings to be printed.
            h_padd (int, optional): Horizontal Padding. Defaults to 4.
            v_padd (int, optional): Vertical Padding. Defaults to 2.
            alignment (str, optional): Alignment of lines. Available options are left, right and center.
        """
        max_length = max(len(line) for line in lines)
        
        half_h_padd = " " * int(h_padd/2)
        half_v_padd = int(v_padd/2)
        
        top_border = "┌" + "─" * (max_length + h_padd) + "┐"
        bottom_border = "└" + "─" * (max_length + h_padd) + "┘"
        
        print(top_border)
        for _ in range(0, half_v_padd):
            print("│" + " " * (max_length + h_padd) + "│")
        
        for line in lines:
            line = (line.ljust(max_length) if alignment == "left" else line.rjust(max_length) if alignment == "right" else line.center(max_length))
            print(f"│{half_h_padd}{line}{half_h_padd}│")
        
        for _ in range(0, half_v_padd):
            print("│" + " " * (max_length + h_padd) + "│")
        print(bottom_border)

    def quote_unicode(self, s: str):
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

    def unquote_unicode(self, s: str):
        if not s:
            return s
        
        s = s.replace("\\0", "\0")
        s = s.replace("\\v", "\v")
        s = s.replace("\\t", "\t")
        s = s.replace("\\r", "\r")
        s = s.replace("\\n", "\n")
        s = s.replace("\\f", "\f")
        s = s.replace("\\b", "\b")
        s = s.replace("\\a", "\a")
        # s = s.replace("\\'", "'")
        # s = s.replace('\\"', '"')
        # s = s.replace("\\\\", "\\")
        
        if "  " in s or "'" in s or "\n" in s or "\r" in s or "\t" in s or (s and (s[0] == " " or s[-1] == " ")):
            s = f'"{s}"'
        
        if s and s[0] == "?":
            s = f"\\{s}"
        
        return s

class Config:
    def __init__(self, config_file="config.json", config_folder=f"veydzh3r\\{APP_NAME}"):
        self.config_path = self.get_config_path(config_file, config_folder)
        self.config = {}
        self.load()
    
    def get_config_path(self, file, folder):
        if platform.system() == "Windows":
            base_dir = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base_dir = Path.home() / ".config"
        
        app_dir = base_dir / folder
        app_dir.mkdir(parents=True, exist_ok=True)
        
        return app_dir / file
    
    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Config file corrupted, using defaults. Error: {e}")
                self.config = self.get_defaults()
                self.save()
        else:
            self.config = self.get_defaults()
            self.save()
    
    def get_defaults(self):
        return {
            "detailed_export": False,
            "detailed_import": True,
            "log_level": "INFO"
        }
    
    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save()

if __name__ == "__main__":
    try:
        app = XMLtoSTRINGS()
    except Exception as e:
        # Final fallback logging
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Critical error starting application: {e}")
        print(f"Critical error: {e}")
        exit(1)