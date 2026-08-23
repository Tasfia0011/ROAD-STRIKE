import re

def update_file():
    with open('423_Project.py.bak', 'r') as f:
        content = f.read()

    # The functions we want to replace completely
    funcs_to_replace = [
        'draw_text', 'draw_mpl_line', 'draw_connected_wheel', 'setupCamera', 'get_color', 
        'draw_traffic_light', 'draw_environment', 'draw_road', 'draw_traffic', 
        'draw_analog_dial', 'draw_dashboard', 'showScreen'
    ]

    # Use regex to remove these functions. 
    # A function block is from "def name(" until the next "def " or end of file.
    # Note: 'draw_player_bike', 'draw_intersection', 'draw_signal', 'draw_red_screen' are also in the original
    funcs_to_replace.extend(['draw_player_bike', 'draw_intersection', 'draw_signal', 'draw_red_screen'])

    for func in funcs_to_replace:
        pattern = r"def " + func + r"\(.*?\):.*?(?=def |\Z)"
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    # We also want to inject our new imports and variables at the top.
    # We will just write our new drawing functions and append the original idle/keys.
    
    with open('423_Project.py', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    update_file()
