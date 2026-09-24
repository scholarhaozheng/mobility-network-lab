# Code and data boundaries for the scalable-tool candidate

The staged tool code and synthetic generic fixtures follow the repository's MIT code notice in `LICENSE`. That notice does not grant rights to external feeds or all source data used in the private Boston computation.

The accepted Central Boston physical geography descends from GMNS Plus `21_Boston` (Apache-2.0), source commit `116447ab641cca1ed34797d019c8e704063393c3`, as attributed in the existing public case. The versioned flow figures and plotted physical-link source tables in this candidate use those physical links with newly modeled conditional HBW road flow; they are not observed traffic. Keep that geography attribution when displaying the new maps.

Raw MBTA GTFS, the larger regional/person OD source, OSM source extract, local routing environment and solver binary are not included in `public_candidates/`. Their original providers and terms remain separate. The private delivery contains exact compact prepared inputs and a source asset index for local reproducibility; it is not a blanket public redistribution grant for original feeds. A user of Route A may supply independently licensed GMNS network and vehicle OD without any Boston raw dependency.
