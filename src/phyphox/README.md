# Core phyphox Sources

The seven root files in `experiments/*.phyphox` are generated from
`src/phyphox/*.phyphox.xml`.

Source files use XInclude for shared data containers and Bluetooth mappings in
`src/phyphox/includes/`. The file format does not provide fragment inclusion
for individual attributes or translation strings, so view and translation
content is repeated where required.

## Source ownership

Edit the `.phyphox.xml` sources and shared include files. Do not edit the
matching generated files as independent sources.

Rebuild and verify from the repository root:

```sh
make build
make check-generated
make validate
```

`make build` intentionally updates tracked files in `experiments/`.
`make check-generated` rebuilds into a temporary directory and compares the
result byte for byte.

## Attribution

- Original authors: Gautier Creutzer and Frédéric Bouquet, La Physique
  Autrement, Laboratoire de Physique des Solides, Université Paris-Saclay
- Revisions 1.1 and 1.2: Sebastian J. Spicker and Frédéric Bouquet, including
  German translation, units, views, axis labels, and consistency changes
- [Related English and French material](https://vulgarisation.fr/?lang=en)
- [Related German material](https://astro-lab.app/arduino-und-phyphox/)
- Related project: phyphox, RWTH Aachen University

## License status

Source and generated file comments state `LGPL-3.0-or-later`. The root
`LICENSE` contains GNU GPL version 3 text. The relationship between these
statements has not been documented. Astronomy content authorship and embedded
asset provenance also require confirmation. Public distribution remains
blocked until maintainers document the component-level terms.
