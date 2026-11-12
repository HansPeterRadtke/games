# Offline practice vocabulary

German forms come from the Debian wngerman package (20161207-12), built from [igerman98](https://www.j3e.de/ispell/igerman98/dict/). The German word data is distributed under GPL version two or later. The upstream and Debian notices are in [de-NOTICE.txt](de-NOTICE.txt) and the license is in [COPYING-de.txt](COPYING-de.txt).

English forms come from [SCOWL](https://wordlist.aspell.net/) in the Debian scowl package (2020.12.07-2). The build takes the English, American and British word lists through size 70, excluding the abbreviation, proper name and numeral lists. The full terms and credits for the English word data are in [en-NOTICE.txt](en-NOTICE.txt).

The checked-in word banks are generated, editable source data in a prefix-length text format. Run `python3 tools/build_vocabulary.py` with the wngerman and scowl packages and Python wordfreq 3.1.1 installed to rebuild. The script merges duplicate forms, folds German noun capitals and removes punctuation, inaccessible letters, initialisms and most abbreviations without vowels. It includes a small set of supplemental spellings. Inflections, compounds and regional spellings are distinct practice words. Each word is stored at the first level where its letters are available.

A separate familiarity list uses the twenty thousand most frequent forms in each language from Robyn Speer’s [wordfreq](https://doi.org/10.5281/zenodo.7199437) 3.1.1. The generated familiarity lists are distributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Filtering and formatting are described in the build script. The [source credits](frequency-NOTICE.txt) include OpenSubtitles and the freely available SUBTLEX data by Marc Brysbaert and collaborators.
