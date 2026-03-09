import ebooklib
import re
from ebooklib import epub

def count_words_in_epub(file_path):
    book = epub.read_epub("/Users/flofonic/Documents/Blackout/blackout/versions/Blackout_Weak_Signals_v1.11.28.epub")
    total_words = 0
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            text = item.get_body_content()
            words = re.findall(r'\w+', text.decode('utf-8'))
            total_words += len(words)
    
    return total_words

epub_file = 'path/to/your/book.epub'
print(f'Total words: {count_words_in_epub(epub_file)}')
