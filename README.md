# drive-filmy

Strona do oglądania filmów z folderu na Dysku Google: pełne nazwy plików,
odtwarzanie w stronie i zaznaczanie obejrzanych.

## Użycie

```
https://drive-filmy.vercel.app/?folder=<link do folderu na Dysku Google>
```

Folder musi być udostępniony każdemu, kto ma link. Adres z `?folder=` można
wysłać dalej: u każdego otworzy się ten sam folder. Bez `?folder=` strona
prosi o wklejenie linku.

## Jak to działa

- `api/list.py` (funkcja Vercel, sam Python bez zależności) czyta publiczny
  widok folderu (`embeddedfolderview`) bez klucza API Google, razem
  z podfolderami, i zwraca listę filmów jako JSON. CDN trzyma wynik 5 minut,
  więc nowe filmy pojawiają się z takim opóźnieniem.
- `index.html` odtwarza film w `<video>` prosto z linku pobierania Dysku
  (przez CORS), więc po przekroczeniu 90% długości albo na końcu sam oznacza
  go jako obejrzany i pamięta miejsce przerwania. Plik, którego przeglądarka
  nie odtworzy, przechodzi do odtwarzacza Dysku Google; taki oznacza się
  ręcznie.
- Postęp jest w `localStorage` przeglądarki: każdy oglądający ma swój, na
  każdym urządzeniu osobno.

Widok folderu nie jest oficjalnym API Google. Jeśli Google go zmieni,
`api/list.py` trzeba będzie dopasować.
