# Offline practice vocabulary

German forms come from the Debian wngerman package (20161207-12), built from [igerman98](https://www.j3e.de/ispell/igerman98/dict/). The German word data is distributed under GPL version two or later. The upstream and Debian notices are in [de-NOTICE.txt](de-NOTICE.txt) and the license is in [COPYING-de.txt](COPYING-de.txt).

English forms come from [SCOWL](https://wordlist.aspell.net/) in the Debian scowl package (2020.12.07-2). The build takes the English, American and British word lists through size 70, excluding the abbreviation, proper name and numeral lists. The full terms and credits for the English word data are in [en-NOTICE.txt](en-NOTICE.txt).

The [German](practice-de.txt) and [English](practice-en.txt) practice lists supply every word at levels six through twelve and every prompt shorter than five letters. For example, German level ten includes *Jagd*, *Ölfass* and *Kajak*. The practice display uses lowercase throughout. The restricted alphabet has no approved word for *ä* at this point, so the exercise gives the letter its own keycap. At the next level, *Ära* becomes available.

For longer words beyond the starter alphabet, the build takes only entries present in all three sources for the language: the spelling word list, the MyThes thesaurus headword index, and the 25,000 most frequent entries in wordfreq. The German headword index is OpenThesaurus in Debian mythes-de 20160424-4. The English index is supplied by LibreOffice in mythes-en-us 1:24.2.1-1. [German thesaurus notice](de-thesaurus-NOTICE.txt) · [German thesaurus license](COPYING-thesaurus-de.txt) · [English thesaurus notice](en-thesaurus-NOTICE.txt)

Frequency data comes from Robyn Speer’s [wordfreq](https://doi.org/10.5281/zenodo.7199437) 3.1.1, whose data files use [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The selection and encoding are adapted for keyboard practice. The [source credits](frequency-NOTICE.txt) include OpenSubtitles and the freely available SUBTLEX data by Marc Brysbaert and collaborators.

Run `python3 tools/build_vocabulary.py` with wngerman, scowl, mythes-de, mythes-en-us and Python wordfreq 3.1.1 installed to regenerate both language banks. Each word is stored at the first level where it can be typed. The browser uses only the generated practice banks.
