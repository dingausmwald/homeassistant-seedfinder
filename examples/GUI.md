# Example GUI

This is a very rough example on what I have set up to create the HA GUI.

![Example](../images/openplantbook.gif)


## Helpers

We need some helpers to save the search results and trigger the automatons

### input_text
```
seedfinder_search:
  name: Search Seedfinder
```

### input_select
```
seedfinder_searchresults:
  name: Seedfinder Search Results
  options:
    - "Search first"
```
### input_button
```
seedfinder_clear_cache:
  name: Clear Seedfinder Cache
```

## Automations

These automations trigger when the different helpers are modified.

Initiate a search when the input_text helper is modified

```
alias: Search Seedfinder
trigger:
  - platform: state
    entity_id: input_text.seedfinder_search
action:
  - service: seedfinder.search
    data:
      alias: "{{ states('input_text.seedfinder_search') }}"

```

Populate the input_select when a search result is ready

```
alias: Populate Seedfinder Dropdown
trigger:
  - platform: state
    entity_id: seedfinder.search_result
action:
  - service: input_select.set_options
    data:
      entity_id: input_select.seedfinder_searchresults
      options: |
        {% if states('seedfinder.search_result') | int(default=0) > 0 %}
          {{ states.seedfinder.search_result.attributes | list }}
        {% else %}
          [ "No plants found"]
        {% endif %}

```

Get details from Seedfinder when an option in the dropdown is selected

```
alias: Get Info From Seedfinder
trigger:
  - platform: state
    entity_id: input_select.seedfinder_searchresults
action:
  - service: seedfinder.get
    data:
      species: "{{ states('input_select.seedfinder_searchresults') }}"

```

Clear the cache when the button is pressed

```

alias: Clear Seedfinder cache
trigger:
  - platform: state
    entity_id:
      - input_button.seedfinder_clear_cache
action:
  - service: seedfinder.clean_cache
    data:
      hours: 0
```



## Lovelace

I use two cards.  One for the search and search results, and one to display the info about a single plant.

```
type: entities
title: Search Seedfinder
entities:
  - entity: input_text.seedfinder_search
  - entity: seedfinder.search_result
  - entity: input_select.seedfinder_searchresults
  - entity: input_button.seedfinder_clear_cache
```

```
type: markdown
title: Plant info
content: |

  {% set plant = "seedfinder." + states('input_select.seedfinder_searchresults') | replace(" ", "_") | replace("'", "") | replace(".", "") %}
  {% if states(plant) == "unknown" %}
  # Search for a plant
  {% else %}
  # {{ state_attr(plant, 'display_pid') }}
  {% set min_dli = ((state_attr(plant, 'min_light_mmol') | float(default=0) * 0.0036)) | round(0, default=0) %}
  {% set max_dli = ((state_attr(plant, 'max_light_mmol') | float(default=0) * 0.0036)) | round(0, default=0) %}

  ![Image]({{ state_attr(plant, 'image_url') | urlencode }})

  _{{ state_attr(plant, 'pid') }}_

  ## Thresholds

  |                      | Min                                       |    | Max                                       |      |
  |----------------------|------------------------------------------:|----|------------------------------------------:|------|
  | Moisture             | {{ state_attr(plant, 'min_soil_moist') }} |    | {{ state_attr(plant, 'max_soil_moist') }} |%     |
  | Conductitivty        | {{ state_attr(plant, 'min_soil_ec') }}    |    | {{ state_attr(plant, 'max_soil_ec') }}    |μS/cm |
  | Temperature          | {{ state_attr(plant, 'min_temp') }}       |    | {{ state_attr(plant, 'max_temp') }}       |°C    |
  | Humidity             | {{ state_attr(plant, 'min_env_humid') }}  |    | {{ state_attr(plant, 'max_env_humid') }}  |%     |
  | Illumination         | {{ state_attr(plant, 'min_light_lux') }}  |    | {{ state_attr(plant, 'max_light_lux') }}  |lx    |
  | Daily Light Integral | {{ min_dli }}                             |    | {{ max_dli }}                             |mol/d⋅m²|
  {% endif %}
```
