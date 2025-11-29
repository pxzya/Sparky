import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Modifier masks
MOD_NONE = 0x00
MOD_CTRL = 0x01
MOD_SHIFT = 0x02
MOD_ALT = 0x04
MOD_GUI = 0x08  # Windows (GUI) key

# Keycodes set (partial, extend as needed)
KEY_CODES = {
    'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08, 'f': 0x09, 'g': 0x0A,
    'h': 0x0B, 'i': 0x0C, 'j': 0x0D, 'k': 0x0E, 'l': 0x0F, 'm': 0x10, 'n': 0x11,
    'o': 0x12, 'p': 0x13, 'q': 0x14, 'r': 0x15, 's': 0x16, 't': 0x17, 'u': 0x18,
    'v': 0x19, 'w': 0x1A, 'x': 0x1B, 'y': 0x1C, 'z': 0x1D,

    '1': 0x1E, '2': 0x1F, '3': 0x20, '4': 0x21, '5': 0x22,
    '6': 0x23, '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,

    'ENTER': 0x28, 'ESC': 0x29, 'BACKSPACE': 0x2A, 'TAB': 0x2B, 'SPACE': 0x2C,
    'MINUS': 0x2D, 'EQUAL': 0x2E, 'LEFTBRACE': 0x2F, 'RIGHTBRACE': 0x30, 'BACKSLASH': 0x31,
    'SEMICOLON': 0x33, 'APOSTROPHE': 0x34, 'GRAVE': 0x35, 'COMMA': 0x36, 'DOT': 0x37,
    'SLASH': 0x38,
}

SHIFT_CHARACTERS = {
    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
    '_': 'MINUS', '+': 'EQUAL', '{': 'LEFTBRACE', '}': 'RIGHTBRACE',
    '|': 'BACKSLASH', ':': 'SEMICOLON', '"': 'APOSTROPHE',
    '~': 'GRAVE', '<': 'COMMA', '>': 'DOT', '?': 'SLASH'
}

def char_to_keycode(c):
    if c.isalpha():
        mod = MOD_SHIFT if c.isupper() else MOD_NONE
        key = KEY_CODES[c.lower()]
        return (mod, key)
    elif c.isdigit():
        return (MOD_NONE, KEY_CODES[c])
    elif c == ' ':
        return (MOD_NONE, KEY_CODES['SPACE'])
    elif c in SHIFT_CHARACTERS:
        mod = MOD_SHIFT
        base_char = SHIFT_CHARACTERS[c]
        key = KEY_CODES[base_char]
        return (mod, key)
    else:
        symbol_map = {
            '-': 'MINUS', '=': 'EQUAL', '[': 'LEFTBRACE', ']': 'RIGHTBRACE',
            '\\': 'BACKSLASH', ';': 'SEMICOLON', '\'': 'APOSTROPHE', '`': 'GRAVE',
            ',': 'COMMA', '.': 'DOT', '/': 'SLASH'
        }
        if c in symbol_map:
            return (MOD_NONE, KEY_CODES[symbol_map[c]])
        return (MOD_NONE, KEY_CODES['SPACE'])  # fallback

def convert_duckyscript_to_arduino(code: str, layout='US', sketch_name='duckify_sketch'):
    lines = code.strip().splitlines()
    output = []
    output_message = ("""
//+-----------------------------------+
//|This sketch is converted by Sparky.|
//|            .-------.              |
//|         By | PXZYA |              |
//|            '-------'              |
//+-----------------------------------+
""")
    output.append(output_message)
    output.append(f'//-> Platform: Digispark')
    output.append(f'//-> Keyboard Layout: {layout}\n')
    output.append('#include "DigiKeyboard.h"\n')

    string_arrays = []
    string_index = 0
    setup_lines = []

    default_delay = 0
    has_default_delay = False

    def progmem_array(string):
        arr = []
        for c in string:
            mod, key = char_to_keycode(c)
            arr.append(mod)
            arr.append(key)
        return arr

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('//'):
            # Preserve comments
            if stripped.startswith('//'):
                output.append(stripped)
            continue

        parts = stripped.split()
        cmd = parts[0].upper()

        if cmd == 'DELAY':
            ms = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            setup_lines.append(f'    DigiKeyboard.delay({ms}); // DELAY {ms}')
            continue

        if cmd == 'DEFAULTDELAY' or cmd == 'DEFAULT_DELAY':
            ms = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            default_delay = ms
            has_default_delay = True
            setup_lines.append(f'    DigiKeyboard.delay({ms}); // DEFAULTDELAY {ms}')
            continue

        if cmd == 'STRING':
            string_content = stripped[7:]
            array_name = f'key_arr_{string_index}'
            string_index += 1
            bytes_arr = progmem_array(string_content)
            bytes_str = ', '.join(str(b) for b in bytes_arr)
            output.append(f'// {string_content}')
            output.append(f'const uint8_t {array_name}[] PROGMEM = {{{bytes_str}}};')
            setup_lines.append(f'    duckyString({array_name}, sizeof({array_name})); // STRING {string_content}')
            if has_default_delay:
                setup_lines.append(f'    DigiKeyboard.delay({default_delay});')
            continue

        if cmd == 'ENTER':
            setup_lines.append(f'    DigiKeyboard.sendKeyStroke({KEY_CODES["ENTER"]}, 0); // ENTER')
            if has_default_delay:
                setup_lines.append(f'    DigiKeyboard.delay({default_delay});')
            continue

        # Handle modifiers + key combos like GUI r
        modifiers = 0
        keycode = None
        mod_map = {'CTRL': MOD_CTRL, 'CONTROL': MOD_CTRL, 'ALT': MOD_ALT, 'SHIFT': MOD_SHIFT, 'GUI': MOD_GUI, 'WINDOWS': MOD_GUI}

        # Count modifiers in all but last token, last token is key
        for p in parts[:-1]:
            if p.upper() in mod_map:
                modifiers |= mod_map[p.upper()]
        last_token = parts[-1].lower()

        if last_token in KEY_CODES:
            keycode = KEY_CODES[last_token]
        elif len(last_token) == 1:
            # single char
            mod, kc = char_to_keycode(last_token)
            if mod != MOD_NONE:
                modifiers |= mod
            keycode = kc
        else:
            # unknown fallback to 'r'
            keycode = KEY_CODES['r']

        if cmd.upper() in mod_map and len(parts) == 1:
            # Single modifier press? Ignore for now or could handle if needed
            continue

        # Compose sendKeyStroke for modifier+key
        setup_lines.append(f'    DigiKeyboard.sendKeyStroke({keycode}, {modifiers}); // {" ".join(parts)}')
        if has_default_delay:
            setup_lines.append(f'    DigiKeyboard.delay({default_delay});')

    output.append('')
    output.append('void duckyString(const uint8_t* keys, size_t len) {  ')
    output.append('    for(size_t i=0; i<len; i+=2) {')
    output.append('        DigiKeyboard.sendKeyStroke(pgm_read_byte_near(keys + i+1), pgm_read_byte_near(keys + i));')
    output.append('    }')
    output.append('}\n')

    output.append('void setup() {')
    output.append('    pinMode(1, OUTPUT); // Enable LED')
    output.append('    digitalWrite(1, LOW); // Turn LED off')
    output.append('    DigiKeyboard.sendKeyStroke(0); // Tell computer no key is pressed\n')

    output.extend(setup_lines)

    output.append('}\n')
    output.append('void loop() {}')
    output.append('')
    output.append('// Created by Sparky')

    return '\n'.join(output)


class sparklingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sparky Script Converter")
        self.root.geometry("470x700")
        self.root.configure(bg="#f4f6f8")
        self.root.iconbitmap("src/icon.ico")


        # Title
        tk.Label(root, text="Sparky", font=("Segoe UI", 18, "bold"), bg="#f4f6f8", fg="#000000").pack(pady=10)
        tk.Label(root, text="Convert Ducky Script → Arduino (.ino) for Digispark", bg="#f4f6f8").pack(pady=5)

        # Layout / name inputs
        frame_top = tk.Frame(root, bg="#f4f6f8")
        frame_top.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(frame_top, text="Keyboard Layout:", bg="#f4f6f8").grid(row=0, column=0, sticky="w")
        self.layout_var = tk.StringVar(value="US")
        ttk.Combobox(frame_top, textvariable=self.layout_var, values=["US", "DE", "FR", "GB"], width=10, state="readonly").grid(row=0, column=1, padx=5)

        tk.Label(frame_top, text="Sketch Name:", bg="#f4f6f8").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.name_var = tk.StringVar(value="sparky_sketch")
        tk.Entry(frame_top, textvariable=self.name_var, width=20).grid(row=0, column=3, padx=5)

        # Script input
        tk.Label(root, text="Ducky Script Input:", bg="#f4f6f8").pack(anchor="w", padx=20)
        self.script_text = tk.Text(root, height=12, font=("Consolas", 11))
        self.script_text.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0, 10))

        # Buttons
        frame_buttons = tk.Frame(root, bg="#f4f6f8")
        frame_buttons.pack(pady=5)
        ttk.Button(frame_buttons, text="Convert", command=self.convert_script).grid(row=0, column=0, padx=10)
        ttk.Button(frame_buttons, text="Save as .ino", command=self.save_file).grid(row=0, column=1, padx=10)
        ttk.Button(frame_buttons, text="Clear", command=self.clear_text).grid(row=0, column=2, padx=10)
        ttk.Button(frame_buttons, text="Exit", command=root.quit).grid(row=0, column=3, padx=10)

        # Output
        tk.Label(root, text="Arduino IDE Sketch Output (.ino):", bg="#f4f6f8").pack(anchor="w", padx=20)
        self.output_text = tk.Text(root, height=18, font=("Consolas", 11), bg="#f0f0f0")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.output_text.configure(state="disabled")

    def convert_script(self):
        script = self.script_text.get("1.0", tk.END)
        layout = self.layout_var.get()
        name = self.name_var.get().strip() or "sparkling_sketch"
        try:
            result = convert_duckyscript_to_arduino(script, layout, name)
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, result)
            self.output_text.configure(state="disabled")
#            messagebox.showinfo("Success", "Conversion complete!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_file(self):
        output = self.output_text.get("1.0", tk.END).strip()
        if not output:
            messagebox.showwarning("No Output", "Please convert a script first.")
            return
        file = filedialog.asksaveasfilename(
            defaultextension=".ino",
            filetypes=[("Arduino Sketch", "*.ino"), ("Text files", "*.txt")],
            title="Save Arduino Sketch"
        )
        if file:
            with open(file, "w", encoding="utf-8") as f:
                f.write(output)
            messagebox.showinfo("Saved", f"File saved as:\n{file}")

    def clear_text(self):
        self.script_text.delete("1.0", tk.END)
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = sparklingGUI(root)
    root.mainloop()
