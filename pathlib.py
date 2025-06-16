from pathlib import Path
import json

current_path = Path()
digit_mapping = {
    1:  'a', 2: 'b', 3: 'c', 4: 'd',
}
#rstring:避免轉義字元 

#json.dump(digit_mapping, open(current_path))