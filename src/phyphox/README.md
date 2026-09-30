# Core phyphox sources

The seven root files in `experiments/*.phyphox` are generated. Their sources
live here, in `src/phyphox/*.phyphox.xml`.

Sources pull in the shared data containers and Bluetooth mappings from
`src/phyphox/includes/` through XInclude. The file format has no way to include
a single attribute or a translation string, so view definitions and translated
text are repeated wherever they are needed.

## Editing

Work on the `.phyphox.xml` sources and the shared include files. Treat the
matching generated files as build output, not as independent sources.

Rebuild and verify from the repository root:

```sh
make build
make check-generated
make validate
```

`make build` intentionally updates tracked files in `experiments/`.
`make check-generated` rebuilds into a temporary directory and compares the
result byte for byte, which is what CI uses to catch drift.

## Attribution

- Original authors: Gautier Creutzer and Frédéric Bouquet, La Physique
  Autrement, Laboratoire de Physique des Solides, Université Paris-Saclay
- Revisions 1.1 and 1.2: Sebastian J. Spicker and Frédéric Bouquet, including
  the German translation, units, views, axis labels, and consistency changes
- [Related English and French material](https://vulgarisation.fr/?lang=en)
- [Related German material](https://astro-lab.app/arduino-und-phyphox/)
- Related project: phyphox, RWTH Aachen University

## License status

Source and generated file comments say `LGPL-3.0-or-later`, while the root
`LICENSE` contains the GNU GPL version 3 text. Nothing in the repository yet
documents how those two statements relate. Astronomy content authorship and
embedded asset provenance also still need confirmation, so public distribution
stays blocked until maintainers document the terms component by component.
