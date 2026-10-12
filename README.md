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
- `index.html` odtwarza film w odtwarzaczu Dysku Google w ramce. Google nie
  pozwala odtwarzać tych plików bezpośrednio w `<video>` na innej stronie
  (403, brak nagłówków CORS), a jego odtwarzacz nie mówi stronie, kiedy film
  się kończy, więc obejrzany oznacza się przyciskiem „Obejrzany, następny”
  albo ptaszkiem na liście. Na wąskim ekranie ramka jest rysowana na 640 px
  szerokości i pomniejszana, bo w węższej odtwarzacz Dysku źle się układa.
- Postęp jest w `localStorage` przeglądarki: każdy oglądający ma swój, na
  każdym urządzeniu osobno.

Widok folderu nie jest oficjalnym API Google. Jeśli Google go zmieni,
`api/list.py` trzeba będzie dopasować.
