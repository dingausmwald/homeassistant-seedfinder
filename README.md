# Seedfinder Integration for Home Assistant

**Cannabis strain data provider for Home Assistant - Part of the Brokkoli Suite**

A Home Assistant integration that fetches cannabis strain information from Seedfinder. Provides online strain data for the [Brokkoli Cannabis Management](https://github.com/dingausmwald/homeassistant-brokkoli) integration.

## 🌱 Features

- Cannabis strain data fetching from Seedfinder database
- Automatic image download and local hosting
- Service calls for strain information retrieval
- Cache management for performance optimization

## 🔧 Installation

### HACS Installation (Recommended)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

1. Add this repository as a Custom Repository in HACS
2. Set the category to "Integration"
3. Click "Install" on the "Seedfinder" card
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/seedfinder/` directory to your `<config>/custom_components/` directory
2. Restart Home Assistant

## 🚀 Setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Seedfinder" and select it
3. Configure image download path (optional)

## 📊 Configuration

### Image Download
- Default path: `/config/www/images/plants`
- Images in `www/` directory are accessible via `/local/` URLs
- Existing files are never overwritten
- Path must exist before configuration

## 📱 Available Services

### `seedfinder.get`
Fetch detailed strain information:

```yaml
service: seedfinder.get
service_data:
  species: White Widow
  breeder: Dutch Passion
```

Results are stored in `seedfinder.white_widow` entity with strain data as attributes.

### `seedfinder.clean_cache`
Clear cached strain data:

```yaml
service: seedfinder.clean_cache
data:
  hours: 24  # optional, defaults to 24
```

## 🎨 Brokkoli Suite Integration

This integration is part of the Brokkoli Suite for cannabis cultivation tracking:

- **[Brokkoli Cannabis Management](https://github.com/dingausmwald/homeassistant-brokkoli)** - Main cannabis monitoring integration
- **[Brokkoli Card](https://github.com/dingausmwald/lovelace-brokkoli-card)** - Lovelace cards for cannabis visualization

## 🤝 Contributing

Contributions are welcome! Please submit pull requests or report issues.

## 📄 License

This project is licensed under the MIT License.

## ☕ Support

<a href="https://www.buymeacoffee.com/dingausmwald" target="_blank">
<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 50px !important;">
</a>
