# Seedfinder integration for Home Assistant

This integration allows fetching plants information from Seedfinder.
It creates a few service calls in Home Assistant to interact with cannabis seedfinder website which
are:

* Get plant details

This is used as a base for the sister-integration https://github.com/dingausmwald/homeassistant-brokkoli

## Installation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

This can be installed manually or through HACS

### Via HACS

* Add this repo as a "Custom repository" with type "Integration"
    * Click HACS in your Home Assistant
    * Click Integrations
    * Click the 3 dots in the top right corner and select "Custom Repositories"
    * Add the URL to this GitHub repository and category "Integration"
* Click "Install" in the new "Seedfinder" card in HACS.
* Wait for install to complete
* Restart Home Assistant

### Manual Installation

* Copy the whole`custom_components/seedfinder/` directory to your server's `<config>/custom_components` directory
* Restart Home Assistant

## Set up

The integration is set up using the GUI.

Go to "Settings" -> "Integrations" in Home Assistant. Click "Add integration" and find "Seedfinder" in the list.

## Configuration

The integration provide the following configuration options:

![image](./images/config-options.png)

### Automatically download images from Seedfinder.

The default path to save the images is `/config/www/images/plants`, but it can be set to any directory you wish.

You need to specify an _existing path_ that the user you are running home assistant as has write access to. If you
specify a relative path (e.g. a path that does not start with a "/", it means a path below your "config" directory. So "
www/images/plants" will mean "&lt;home-assistant-install-directory&gt;/config/www/images/plants".

If the path contains **"www/"** the image_url in plant attributes will also be replaced by a reference to
/local/<path to image>. So if the download path is set to the default "/config/www/images/plants/", the "image_url" of
the species will be replaced with "/local/images/plants/my plant species.jpg".

If the path does _not_ contain **"www/"** the full link to the image in Seedfinder is kept as it is, but the image is
still downloaded to the path you specify.

Existing files will never be overwritten, and the path needs to exist before the integration is configured.

## Examples

Service calls are added by this integration:

### seedfinder.clean_cache

`seedfinder.clean_cache` can be used to manually trigger cleaning of the cache. This service takes an optional parameter, 'hours', which defaults to 24 if not specified.

```yaml
service: seedfinder.clean_cache
```

### seedfinder.get

`seedfinder.get` gets detailed data for a single plant. The result is added to the
entity `seedfinder.<species name>` with parameters for different max/min values set as attributes.

```yaml
service: seedfinder.get
service_data:
  species: white-widow
  breeder: greenhouse-seed-co
```

And the results can be found in `seedfinder.white_widow`:

```jinja2
Details for plant {{ states('seedfinder.white_widow') }}
* Breeder: {{ state_attr('seedfinder.white_widow', 'breeder') }}
* Image: {{ state_attr('seedfinder.white_widow', 'image_url') }}
```

Which gives

Details for plant White Widow

* Breeder: Greenhouse Seed Co.
* Effects: ...
* Image: https://.../white-widow.jpg

### Quick UI example

Just to show how the service calls can be utilized to search the Seedfinder API

![Example](images/openplantbook.gif)

**PS!**

This UI is _not_ part of the integration. It is just an example of how to use the service calls.

An explanation of the UI is available
here: https://github.com/dingausmwald/home-assistant-seedfinder/blob/main/examples/GUI.md

<a href="https://www.buymeacoffee.com/dingausmwald" target="_blank">
<img src="https://user-images.githubusercontent.com/203184/184674974-db7b9e53-8c5a-40a0-bf71-c01311b36b0a.png" style="height: 50px !important;"> 
</a>
