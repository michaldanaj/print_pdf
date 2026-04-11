
## Założenia 

Chciałbym przygotować pdf gotowy do wydruku z
możliwymi opcjami:

- druk dwustronny, ale na drukarce ręcznej. Czyli nieparzyste
  strony przygotować do jednego pliku, a parzyste do drugiego pliku, które będą
  drukowane osobno. Z tym że kolejność drukowania parzystych lub nieparzystych
  powinna być odwrócona, aby nie trzeba było ręcznie przekładać kartek. Trzeba też
  zwrócić uwagę, żeby jeśli liczba stron jest nieparzysta, dopełnić pustą
  stroną.
- dobrze by było móc dodać numer strony do wydruku.
- z opcją czy dwie czy jedna strona na stronie wydruku
- układ pionowy, czy poziomy

## TODO

pdfxup użyć zamiast pdftk. To odinstalować.


## Opcje komendy

- -i <input.pdf>:  Input PDF file.
- -o <output_name>:  Base name for output file(s) (without extension).
- -d: Prepare for manual duplex printing (creates _odd.pdf and _even.pdf files).
- -n:  Add page numbers to the document.  
- -t:  2 pages per sheet (2-up).
- -l: Landscape orientation for the final output.

## Algorytm

Algorytm powinien działać w kolejności:

1. Bierze pod uwagę ustawienie opcji -l
2. Jeśli jest opcja -t, przygotowuje dwie strony na jednej. Jeśli wyjściowym formatem
   jest landscape, ustawia strony obok siebie, w przeciwnym wypadku jedna nad drugą
4. Jeśli zaznaczona jest opcja -n, dodaje na marginesie dolnym numery stron
3. Jeśli zaznaczona jest opcja -d, układa strony w kolejności:
   - jeśli aktualna (nie oryginalnego dokumentu) liczba stron jest nieparzysta, dodaje 
     na koniec pustą stronę
   - Odwraca kolejność stron parzystych
5. Zapisuje strony parzyste do jednego pliku, a nieparzyste do drugiego


## Nowe - numer strony
Jeszczeni zaimplementowane.

Odpowiedź chata: https://chatgpt.com/share/6995fa49-7200-8005-acc9-b18d4945f177

Odpowiedż claude: https://claude.ai/share/74f8c0aa-ea69-49e7-ae58-d6513a18ccff


