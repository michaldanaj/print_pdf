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
3. Jeśli zaznaczona jest opcja -n, dodaje na marginesie dolnym numery stron
4. Jeśli zaznaczona jest opcja -d, układa strony w kolejności:
   - jeśli aktualna (nie oryginalnego dokumentu) liczba stron jest nieparzysta, dodaje 
     na koniec pustą stronę
   - Odwraca kolejność stron nieparzystych
5. Zapisuje strony parzyste do jednego pliku, a nieparzyste do drugiego


## GUI

Poza linią komend, powinno być GUI.

Tooltipy z tłumaczeniem funkcji.

Po każdej zmianie parametru wydruku podgląd powinien zostać zaktualizowany.

Po zmianie wielkości okna powinno nastąpić dostosowanie podglądu. Wielkość podglądu powinna być dopasowana do wielkości okna w którym jest wyświetlany.

Nazwa pliku, bez ścieżki, z rozszerzeniem, powinna pojawiać się w tooltip.

Powinny być dwa pola na nazwę pliku wyjściowego. Dla duplex, powinny być oba wypełnione, w przeciwnym razie tylko jedna. Opisy pól powinny być adekwatne do roli.

Powinna być możliwość podglądu każdego z plików, wejściowego, jak i osobno każdego z osobnych. 

Powinna być możliwość otwarcia każdego z plików w zewnętrznym programie.

### Lokalizacja plików

Po otwarciu aplikacji, lokalizacją powinno być miejsce skąd aplikacja została otwarta.

Przycisk Zapisz PDF powinien zapisywać w lokalizacji oryginalnego pliku.

Przycisk 'Zapisz w lokalizacji' przed zapisaniem powinien dać możliwość wyboru innej lokalizację na pliki.

Aktualnie wybrana lokalizacja powinna być wypisana z możliwością otwarcia systemowego managera plików w tej lokalizacji.

Otwarcie pliku testowego nie powinno zmieniać lokalizacji.

### Plik testowy

Przycisk "Test" przy polu wejściowym generuje testowy plik PDF z 4 stronami.
Każda strona podzielona jest poziomą linią na dwie połowy.
W górnej połowie napis "strona N, górna połowa", w dolnej "strona N, dolna połowa",
gdzie N to numer strony (1–4).
