# Redis docker deploy

List of databases per application that NAU uses.
This list isn't related with this role, but hey we had to document this somewhere...

The Redis has 10 databases per default, next we list the use of each one.

| DB number | Service                        |
|-----------|--------------------------------|
| 0         | Open edX app celery and Richie |
| 1         | Open edx cache                 |
| 2         | Open edx discovery             |
| 3         | ---                            |
| 4         | ---                            |
| 5         | Open edX ecommerce celery      |
| 6         | Open edX Insights              |
| 7         | Open edX Analytics API         |
| 8         | ---                            |
| 9         | ---                            |