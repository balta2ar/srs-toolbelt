yandex-slovari-tetradki
=======================

yandex-slovari-tetradki is a script to extract words from Yandex Slovari.Tetradki.
I happen to use this translation service and I thought I could help myself to
memorize new words better. One way to do that is to always keep them in front
of your eyes. This script is supposed to extract last N words and display them
nicely in conky.

## Usage

```
$ python2 main.py --num-words 3
en -> ru | conform             согласовывать, сообразовывать
     syn : coordinate, reconcile, fit, yield, accommodate, integrate, tailor, attune, harmonize
     ant : refuse, deny, prevent, reject, disagree, oppose, disobey, disregard, ignore, neglect
     def : 1. a.  To be or act in accord with a set of standards, expectations, or specifications:
           a computer that conforms with the manufacturer's advertising claims; students learning
           to conform to school safety rules. See Synonyms at  correspond.b.  To act, often
           unquestioningly, in accordance with traditional customs or prevailing standards: "Our
           table manners ... change from time to time, but the changes are not reasoned out; we
           merely notice and conform" (Mark Twain).
           2.  To be similar in form or pattern: a windy road that conforms to the coastline; a
           shirt that conforms to different body shapes.

en -> ru | funnel              дымовая труба, дымоход
     syn : pour, filter, transmit, siphon, channel, move, pipe, convey, conduct, carry, pass
     ant : fail, lose
     def : 1. a.  A conical utensil having a small hole or narrow tube at the apex and used to
           channel the flow of a substance, as into a small-mouthed container.b.  Something
           resembling this utensil in shape.
           2.  A shaft, flue, or stack for ventilation or the passage of smoke, especially the
           smokestack of a ship or locomotive.
           1.  To take the shape of a funnel.
           2.  To move through or as if through a funnel: tourists funneling slowly through
           customs.
           1.  To cause to take the shape of a funnel.
           2.  To cause to move through or as if through a funnel.

en -> ru | fraudulent          обманный, жульнический
     syn : deceitful, crooked, dishonest, phony, forged, fake, counterfeit, sham, crafty, criminal
     ant : frank, honest, sincere, trustworthy, truthful, moral, real, open, genuine, true
     def : 1.  Engaging in fraud; deceitful.
           2.  Characterized by, constituting, or gained by fraud: fraudulent business practices.
```

## Screenshot

### Translation & syn & ant

![Colors](http://i.imgur.com/VbO8REc.png)

### Defs

![Definitions](http://i.imgur.com/gePlqoU.png)
