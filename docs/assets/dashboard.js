(function () {
  "use strict";

  const DATA_URL = "assets/regional_data.json";
  const GEOGRAPHY_URL = "assets/globe_geography.json";
  const GLOBE_SCRIPT_URL = "https://cdn.jsdelivr.net/npm/globe.gl@2.46.1/dist/globe.gl.min.js";
  const state = {
    data: null,
    country: "UK",
    areaCode: null,
    metric: "diabetes",
    atlas: null,
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function median(values) {
    const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
    if (!sorted.length) return null;
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  }

  function formatValue(value, digits = 1) {
    if (!Number.isFinite(Number(value))) return "Not available";
    return Number(value).toLocaleString("en-GB", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  function formatCurrency(value, currency) {
    if (!Number.isFinite(Number(value))) return "Not available";
    return new Intl.NumberFormat(currency === "GBP" ? "en-GB" : "en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(value);
  }

  function currentCountry() {
    return state.data.countries[state.country];
  }

  function currentEntity() {
    return currentCountry().entities.find((entity) => entity.area_code === state.areaCode);
  }

  function metricEntities() {
    return currentCountry().entities.filter((entity) => entity.metrics[state.metric]);
  }

  function describeCoverage(history, valueKey = "value") {
    const observed = (history || []).filter((item) => Number.isFinite(Number(item[valueKey])));
    if (!observed.length) return "not available";
    const first = observed[0];
    const latest = observed[observed.length - 1];
    return `${first.period ?? first.year} to ${latest.period ?? latest.year} (${observed.length} observations)`;
  }

  function colourForRatio(ratio) {
    const stops = [
      [67, 133, 232],
      [32, 180, 154],
      [224, 173, 63],
      [240, 109, 92],
    ];
    const scaled = Math.max(0, Math.min(0.999, ratio)) * (stops.length - 1);
    const index = Math.floor(scaled);
    const mix = scaled - index;
    const start = stops[index];
    const end = stops[Math.min(index + 1, stops.length - 1)];
    const rgb = start.map((value, channel) => Math.round(value + (end[channel] - value) * mix));
    return `rgb(${rgb.join(",")})`;
  }

  function loadScript(url) {
    if (window.Globe) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = url;
      script.async = true;
      script.addEventListener("load", resolve, { once: true });
      script.addEventListener("error", () => reject(new Error(`Unable to load ${url}`)), { once: true });
      document.head.appendChild(script);
    });
  }

  function featureCoordinates(geometry) {
    if (geometry.type === "Polygon") return geometry.coordinates;
    if (geometry.type === "MultiPolygon") return geometry.coordinates.flat();
    return [];
  }

  function featureBounds(feature) {
    const points = featureCoordinates(feature.geometry).flat();
    return {
      minLongitude: Math.min(...points.map((point) => point[0])),
      maxLongitude: Math.max(...points.map((point) => point[0])),
      minLatitude: Math.min(...points.map((point) => point[1])),
      maxLatitude: Math.max(...points.map((point) => point[1])),
    };
  }

  function pointInRing(longitude, latitude, ring) {
    let inside = false;
    for (let current = 0, previous = ring.length - 1; current < ring.length; previous = current, current += 1) {
      const currentPoint = ring[current];
      const previousPoint = ring[previous];
      const crosses = (currentPoint[1] > latitude) !== (previousPoint[1] > latitude)
        && longitude < ((previousPoint[0] - currentPoint[0]) * (latitude - currentPoint[1]))
          / (previousPoint[1] - currentPoint[1]) + currentPoint[0];
      if (crosses) inside = !inside;
    }
    return inside;
  }

  function pointInFeature(longitude, latitude, feature) {
    const polygons = feature.geometry.type === "Polygon"
      ? [feature.geometry.coordinates]
      : feature.geometry.coordinates;
    return polygons.some((polygon) => (
      polygon.length > 0
      && pointInRing(longitude, latitude, polygon[0])
      && !polygon.slice(1).some((hole) => pointInRing(longitude, latitude, hole))
    ));
  }

  function atlasLabel(feature) {
    const properties = feature.properties;
    const wrapper = document.createElement("div");
    wrapper.className = "atlas-tooltip";
    const name = document.createElement("strong");
    name.textContent = properties.area_name;
    wrapper.appendChild(name);
    if (feature.atlas?.value != null) {
      const value = document.createElement("span");
      value.textContent = `${formatValue(feature.atlas.value, 1)}% | ${feature.atlas.metricLabel}`;
      wrapper.appendChild(value);
    }
    const geography = document.createElement("small");
    geography.textContent = properties.kind === "region"
      ? properties.country === "USA" ? "United States state" : "England region"
      : "Country boundary";
    wrapper.appendChild(geography);
    return wrapper;
  }

  class RegionalAtlas {
    constructor(container, geography, onSelect) {
      this.container = container;
      this.geography = geography;
      this.onSelect = onSelect;
      this.country = null;
      this.features = [];
      this.hoveredFeature = null;
      this.selectedFeature = null;
      this.reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      this.resize = this.resize.bind(this);
      try {
        if (!window.Globe) throw new Error("Globe.GL is unavailable");
        this.initGlobe();
      } catch (error) {
        console.warn("WebGL atlas unavailable; using the local dotted fallback.", error);
        this.initFallback();
      }
    }

    initGlobe() {
      this.globe = new window.Globe(this.container, {
        animateIn: false,
        rendererConfig: { antialias: true, alpha: true, powerPreference: "high-performance" },
      })
        .backgroundColor("rgba(0,0,0,0)")
        .showGlobe(true)
        .showGraticules(false)
        .showAtmosphere(true)
        .atmosphereColor("#167a5a")
        .atmosphereAltitude(0.085)
        .hexPolygonGeoJsonGeometry((feature) => feature.geometry)
        .hexPolygonUseDots(true)
        .hexPolygonDotResolution((feature) => feature.properties.kind === "region" ? 8 : 6)
        .hexPolygonResolution((feature) => feature.properties.kind === "region" ? 4 : 3)
        .hexPolygonColor((feature) => this.featureColour(feature))
        .hexPolygonAltitude((feature) => this.featureAltitude(feature))
        .hexPolygonMargin((feature) => this.featureMargin(feature))
        .hexPolygonLabel((feature) => atlasLabel(feature))
        .hexPolygonsTransitionDuration(0)
        .enablePointerInteraction(false)
        .showPointerCursor(false);

      const material = this.globe.globeMaterial();
      if (material?.color?.set) material.color.set("#020806");
      if (material?.emissive?.set) material.emissive.set("#020a07");
      if ("emissiveIntensity" in material) material.emissiveIntensity = 0.35;
      if ("shininess" in material) material.shininess = 1;

      const renderer = this.globe.renderer();
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setClearColor(0x000000, 0);

      const controls = this.globe.controls();
      controls.autoRotate = false;
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.enablePan = false;
      controls.minDistance = 135;
      controls.maxDistance = 430;
      this.bindGlobeInteraction();

      this.resizeObserver = new ResizeObserver(this.resize);
      this.resizeObserver.observe(this.container);
      this.visibilityObserver = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) this.globe.resumeAnimation();
        else this.globe.pauseAnimation();
      }, { threshold: 0.01 });
      this.visibilityObserver.observe(this.container);
      this.resize();
    }

    bindGlobeInteraction() {
      this.tooltip = document.createElement("div");
      this.tooltip.className = "atlas-tooltip-shell atlas-manual-tooltip";
      this.tooltip.hidden = true;
      this.container.appendChild(this.tooltip);
      this.pointerStart = null;
      this.pendingPointer = null;
      this.pointerFrame = null;

      this.container.addEventListener("pointerdown", (event) => {
        this.pointerStart = { x: event.clientX, y: event.clientY };
        const rect = this.container.getBoundingClientRect();
        this.updateGlobePointer({
          clientX: event.clientX,
          clientY: event.clientY,
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
        });
        this.tooltip.hidden = true;
      });
      this.container.addEventListener("pointermove", (event) => {
        if (event.buttons) {
          this.tooltip.hidden = true;
          return;
        }
        const rect = this.container.getBoundingClientRect();
        this.pendingPointer = {
          clientX: event.clientX,
          clientY: event.clientY,
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
        };
        if (this.pointerFrame != null) return;
        this.pointerFrame = requestAnimationFrame(() => {
          this.pointerFrame = null;
          this.updateGlobePointer(this.pendingPointer);
        });
      });
      this.container.addEventListener("pointerup", (event) => {
        if (!this.pointerStart) return;
        const distance = Math.hypot(
          event.clientX - this.pointerStart.x,
          event.clientY - this.pointerStart.y
        );
        this.pointerStart = null;
        if (distance < 6) this.selectFeature(this.hoveredFeature);
      });
      this.container.addEventListener("pointerleave", () => {
        this.pointerStart = null;
        this.tooltip.hidden = true;
        this.setHoveredFeature(null);
      });
    }

    updateGlobePointer(pointer) {
      if (!pointer || !this.globe) return;
      const coordinates = this.globe.toGlobeCoords(pointer.x, pointer.y);
      const feature = coordinates ? this.featureAt(coordinates.lng, coordinates.lat) : null;
      this.setHoveredFeature(feature);
      if (!feature) {
        this.tooltip.hidden = true;
        return;
      }
      this.tooltip.replaceChildren(atlasLabel(feature));
      const left = Math.min(pointer.x + 14, Math.max(this.container.clientWidth - 190, 8));
      const top = Math.min(pointer.y + 14, Math.max(this.container.clientHeight - 82, 8));
      this.tooltip.style.left = `${Math.max(left, 8)}px`;
      this.tooltip.style.top = `${Math.max(top, 8)}px`;
      this.tooltip.hidden = false;
    }

    featureAt(longitude, latitude) {
      const candidates = [
        ...this.features.filter((feature) => feature.properties.kind === "region"),
        ...this.features.filter((feature) => feature.properties.kind === "country"),
      ];
      return candidates.find((feature) => {
        const bounds = feature.atlas.bounds;
        return longitude >= bounds.minLongitude
          && longitude <= bounds.maxLongitude
          && latitude >= bounds.minLatitude
          && latitude <= bounds.maxLatitude
          && pointInFeature(longitude, latitude, feature);
      }) || null;
    }

    initFallback() {
      this.isFallback = true;
      this.canvas = document.createElement("canvas");
      this.canvas.className = "atlas-fallback";
      this.container.appendChild(this.canvas);
      this.context = this.canvas.getContext("2d");
      this.fallbackTooltip = document.createElement("div");
      this.fallbackTooltip.className = "atlas-tooltip-shell atlas-manual-tooltip";
      this.fallbackTooltip.hidden = true;
      this.container.appendChild(this.fallbackTooltip);
      this.canvas.addEventListener("pointermove", (event) => this.fallbackPointerMove(event));
      this.canvas.addEventListener("pointerleave", () => {
        this.hoveredFeature = null;
        this.fallbackTooltip.hidden = true;
        this.drawFallback();
      });
      this.canvas.addEventListener("click", () => this.selectFeature(this.hoveredFeature));
      this.resizeObserver = new ResizeObserver(this.resize);
      this.resizeObserver.observe(this.container);
      this.resize();
    }

    setData(country, entities, metric, selectedCode) {
      const countryChanged = country !== this.country;
      this.country = country;
      const entityByCode = new Map(entities.map((entity) => [entity.area_code, entity]));
      const values = entities
        .filter((entity) => entity.metrics[metric])
        .map((entity) => Number(entity.metrics[metric].latest_value));
      const min = Math.min(...values);
      const max = Math.max(...values);
      const regions = this.geography.regions[country].features;
      regions.forEach((feature) => {
        const entity = entityByCode.get(feature.properties.area_code);
        const metricData = entity?.metrics[metric];
        const value = metricData ? Number(metricData.latest_value) : null;
        feature.atlas = {
          role: "region",
          bounds: featureBounds(feature),
          entity,
          metricLabel: metricData?.label || "No matched indicator",
          value,
          ratio: value == null || max === min ? 0.5 : (value - min) / (max - min),
          selected: feature.properties.area_code === selectedCode,
        };
      });
      this.geography.countries.features.forEach((feature) => {
        feature.atlas = { role: "world", selected: false, bounds: featureBounds(feature) };
      });

      const countries = this.geography.countries.features.filter((feature) => (
        !(country === "USA" && feature.properties.area_code === "USA")
      ));
      this.features = [...countries, ...regions];
      this.selectedFeature = regions.find((feature) => feature.atlas.selected) || null;
      this.hoveredFeature = null;
      if (this.tooltip) this.tooltip.hidden = true;

      if (this.globe) {
        this.globe.hexPolygonsData(this.features);
        this.refreshVisualState();
        if (countryChanged) this.focusCountry(country);
      } else {
        this.fallbackRotation = country === "USA" ? -97 : -3;
        this.buildFallbackSamples();
        this.drawFallback();
      }
    }

    focusCountry(country) {
      const pointOfView = country === "USA"
        ? { lat: 38, lng: -98, altitude: 1.85 }
        : { lat: 53, lng: -2.5, altitude: 1.68 };
      this.globe.pointOfView(pointOfView, this.reducedMotion ? 0 : 950);
    }

    featureColour(feature) {
      if (feature === this.hoveredFeature) return "#8dffd0";
      if (feature.atlas?.selected) return "#57efb4";
      if (feature.atlas?.role === "region" && feature.atlas.value != null) {
        return colourForRatio(feature.atlas.ratio);
      }
      return "#4b786f";
    }

    featureAltitude(feature) {
      if (feature === this.hoveredFeature) return 0.032;
      if (feature.atlas?.selected) return 0.021;
      if (feature.atlas?.role === "region") return 0.009 + feature.atlas.ratio * 0.004;
      return 0.002;
    }

    featureMargin(feature) {
      if (feature === this.hoveredFeature) return 0.28;
      if (feature.atlas?.selected) return 0.34;
      return feature.atlas?.role === "region" ? 0.46 : 0.62;
    }

    setHoveredFeature(feature) {
      if (feature === this.hoveredFeature) return;
      this.hoveredFeature = feature || null;
      this.refreshVisualState();
    }

    selectFeature(feature) {
      if (!feature || !this.onSelect) return;
      const properties = feature.properties;
      if (properties.kind === "region") {
        this.onSelect(properties.country, properties.area_code);
      } else if (properties.area_code === "USA") {
        this.onSelect("USA", null);
      } else if (properties.area_code === "GBR") {
        this.onSelect("UK", null);
      }
    }

    refreshVisualState() {
      if (!this.globe) return;
      this.globe
        .hexPolygonColor((feature) => this.featureColour(feature))
        .hexPolygonAltitude((feature) => this.featureAltitude(feature))
        .hexPolygonMargin((feature) => this.featureMargin(feature));
    }

    buildFallbackSamples() {
      const samples = [];
      const countries = this.features.filter((feature) => feature.properties.kind === "country");
      for (let latitude = -58; latitude <= 84; latitude += 2.2) {
        for (let longitude = -180; longitude < 180; longitude += 2.2) {
          const feature = countries.find((candidate) => pointInFeature(longitude, latitude, candidate));
          if (feature) samples.push({ latitude, longitude, feature });
        }
      }
      const step = this.country === "USA" ? 0.85 : 0.18;
      this.features
        .filter((feature) => feature.properties.kind === "region")
        .forEach((feature) => {
          const coordinates = featureCoordinates(feature.geometry).flat();
          const longitudes = coordinates.map((point) => point[0]);
          const latitudes = coordinates.map((point) => point[1]);
          const bounds = {
            minLongitude: Math.min(...longitudes),
            maxLongitude: Math.max(...longitudes),
            minLatitude: Math.min(...latitudes),
            maxLatitude: Math.max(...latitudes),
          };
          for (let latitude = bounds.minLatitude; latitude <= bounds.maxLatitude; latitude += step) {
            for (let longitude = bounds.minLongitude; longitude <= bounds.maxLongitude; longitude += step) {
              if (pointInFeature(longitude, latitude, feature)) samples.push({ latitude, longitude, feature });
            }
          }
        });
      this.fallbackSamples = samples;
    }

    drawFallback() {
      if (!this.context || !this.fallbackSamples) return;
      const ctx = this.context;
      const width = this.canvas.clientWidth;
      const height = this.canvas.clientHeight;
      ctx.clearRect(0, 0, width, height);
      const cx = width * 0.5;
      const cy = height * 0.5;
      const radius = Math.min(width, height) * 0.39;
      const core = ctx.createRadialGradient(cx - radius * 0.25, cy - radius * 0.25, 0, cx, cy, radius);
      core.addColorStop(0, "#102923");
      core.addColorStop(1, "#050d0b");
      ctx.fillStyle = core;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.save();
      ctx.shadowColor = "rgba(69, 244, 171, 0.55)";
      ctx.shadowBlur = 20;
      ctx.strokeStyle = "rgba(82, 233, 177, 0.36)";
      ctx.lineWidth = 1.2;
      ctx.stroke();
      ctx.restore();

      this.fallbackSamples.forEach((sample) => {
        const projected = this.projectFallback(sample.longitude, sample.latitude, cx, cy, radius);
        if (!projected) return;
        const feature = sample.feature;
        ctx.fillStyle = this.featureColour(feature);
        const dotRadius = feature.atlas?.role === "region" ? 1.55 : 1.05;
        ctx.beginPath();
        ctx.arc(projected.x, projected.y, dotRadius, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    projectFallback(longitude, latitude, cx, cy, radius) {
      const lambda = (longitude - this.fallbackRotation) * (Math.PI / 180);
      const phi = latitude * (Math.PI / 180);
      const depth = Math.cos(phi) * Math.cos(lambda);
      if (depth <= 0) return null;
      return {
        x: cx + radius * Math.cos(phi) * Math.sin(lambda),
        y: cy - radius * Math.sin(phi),
      };
    }

    fallbackPointerMove(event) {
      if (!this.fallbackSamples) return;
      const rect = this.canvas.getBoundingClientRect();
      const width = this.canvas.clientWidth;
      const height = this.canvas.clientHeight;
      const cx = width * 0.5;
      const cy = height * 0.5;
      const radius = Math.min(width, height) * 0.39;
      const normalX = (event.clientX - rect.left - cx) / radius;
      const normalY = (cy - (event.clientY - rect.top)) / radius;
      const radial = normalX * normalX + normalY * normalY;
      let feature = null;
      if (radial <= 1) {
        const depth = Math.sqrt(1 - radial);
        const latitude = Math.asin(normalY) * (180 / Math.PI);
        let longitude = Math.atan2(normalX, depth) * (180 / Math.PI) + this.fallbackRotation;
        longitude = ((longitude + 540) % 360) - 180;
        const regions = this.features.filter((candidate) => candidate.properties.kind === "region");
        feature = regions.find((candidate) => pointInFeature(longitude, latitude, candidate))
          || this.features.find((candidate) => (
            candidate.properties.kind === "country" && pointInFeature(longitude, latitude, candidate)
          ));
      }
      if (feature !== this.hoveredFeature) {
        this.hoveredFeature = feature || null;
        this.drawFallback();
      }
      if (feature) {
        this.fallbackTooltip.replaceChildren(atlasLabel(feature));
        this.fallbackTooltip.style.position = "absolute";
        this.fallbackTooltip.style.left = `${event.clientX - rect.left + 12}px`;
        this.fallbackTooltip.style.top = `${event.clientY - rect.top + 12}px`;
        this.fallbackTooltip.hidden = false;
      } else {
        this.fallbackTooltip.hidden = true;
      }
    }

    resize() {
      const width = Math.max(this.container.clientWidth, 1);
      const height = Math.max(this.container.clientHeight, 1);
      if (this.globe) {
        this.globe.width(width).height(height);
      } else if (this.canvas && this.context) {
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        this.canvas.width = Math.round(width * ratio);
        this.canvas.height = Math.round(height * ratio);
        this.context.setTransform(ratio, 0, 0, ratio, 0, 0);
        this.drawFallback();
      }
    }
  }

  function makeSvg(width, height) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("preserveAspectRatio", "none");
    return svg;
  }

  function svgElement(name, attributes = {}) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  function drawLineChart(container, history, forecastPoints, options = {}) {
    container.replaceChildren();
    const width = 820;
    const height = 340;
    const margin = { top: 24, right: 26, bottom: 42, left: 58 };
    const observed = history.map((item) => ({ year: Number(item.year), value: Number(options.valueKey ? item[options.valueKey] : item.value) }));
    const forecast = (forecastPoints || []).map((item) => ({
      year: Number(item.year),
      value: Number(item.forecast_value),
      lower: Number(item.lower),
      upper: Number(item.upper),
    }));
    const all = [...observed, ...forecast];
    if (!all.length) {
      container.textContent = "No data available for this view.";
      return;
    }

    const years = all.map((item) => item.year);
    const values = all.flatMap((item) => [item.value, item.lower, item.upper]).filter(Number.isFinite);
    let minValue = Math.min(...values);
    let maxValue = Math.max(...values);
    const padding = Math.max((maxValue - minValue) * 0.15, maxValue * 0.03, 0.5);
    minValue = Math.max(options.zeroFloor ? 0 : -Infinity, minValue - padding);
    maxValue += padding;
    const minYear = Math.min(...years);
    const maxYear = Math.max(...years);
    const x = (year) => margin.left + ((year - minYear) / Math.max(maxYear - minYear, 1)) * (width - margin.left - margin.right);
    const y = (value) => margin.top + ((maxValue - value) / Math.max(maxValue - minValue, 1)) * (height - margin.top - margin.bottom);
    const svg = makeSvg(width, height);

    for (let index = 0; index <= 4; index += 1) {
      const value = minValue + ((maxValue - minValue) * index) / 4;
      const yPos = y(value);
      svg.appendChild(svgElement("line", { x1: margin.left, y1: yPos, x2: width - margin.right, y2: yPos, class: "grid-line" }));
      const label = svgElement("text", { x: margin.left - 10, y: yPos + 3, "text-anchor": "end", class: "axis-label" });
      label.textContent = options.currency ? formatCurrency(value, options.currency).replace(/\.00$/, "") : formatValue(value, 1);
      svg.appendChild(label);
    }

    const tickYears = [...new Set([minYear, ...observed.map((item) => item.year), maxYear])];
    const desiredTicks = tickYears.length > 9 ? tickYears.filter((_, index) => index % Math.ceil(tickYears.length / 7) === 0) : tickYears;
    desiredTicks.forEach((year) => {
      const label = svgElement("text", { x: x(year), y: height - 13, "text-anchor": "middle", class: "axis-label" });
      label.textContent = year;
      svg.appendChild(label);
    });

    if (forecast.length) {
      const bandPoints = [
        ...forecast.map((item) => `${x(item.year)},${y(item.upper)}`),
        ...forecast.slice().reverse().map((item) => `${x(item.year)},${y(item.lower)}`),
      ].join(" ");
      svg.appendChild(svgElement("polygon", { points: bandPoints, class: "forecast-band" }));
    }

    const observedPoints = observed.map((item) => `${x(item.year)},${y(item.value)}`).join(" ");
    svg.appendChild(svgElement("polyline", { points: observedPoints, class: "observed-line" }));
    observed.forEach((item) => {
      const circle = svgElement("circle", { cx: x(item.year), cy: y(item.value), r: 4, class: "observed-dot" });
      const title = svgElement("title");
      title.textContent = `${item.year}: ${options.currency ? formatCurrency(item.value, options.currency) : formatValue(item.value, 1)}`;
      circle.appendChild(title);
      svg.appendChild(circle);
    });

    if (forecast.length) {
      const bridge = [observed[observed.length - 1], ...forecast];
      const forecastLinePoints = bridge.map((item) => `${x(item.year)},${y(item.value)}`).join(" ");
      svg.appendChild(svgElement("polyline", { points: forecastLinePoints, class: "forecast-line" }));
      forecast.forEach((item) => {
        const circle = svgElement("circle", { cx: x(item.year), cy: y(item.value), r: 4, class: "forecast-dot" });
        const title = svgElement("title");
        title.textContent = `${item.year} forecast: ${formatValue(item.value, 1)} (${formatValue(item.lower, 1)}-${formatValue(item.upper, 1)})`;
        circle.appendChild(title);
        svg.appendChild(circle);
      });
    }

    container.appendChild(svg);
  }

  function drawComparisonChart(container, series, options = {}) {
    container.replaceChildren();
    const width = 820;
    const height = 300;
    const margin = { top: 22, right: 26, bottom: 42, left: 58 };
    const cleanSeries = series.map((item) => ({
      ...item,
      points: item.points
        .map((point) => ({ year: Number(point.year), value: Number(point.value) }))
        .filter((point) => Number.isFinite(point.year) && Number.isFinite(point.value))
        .sort((left, right) => left.year - right.year),
    }));
    const points = cleanSeries.flatMap((item) => item.points);
    if (!points.length) {
      container.textContent = "No data available for this view.";
      return;
    }

    const years = points.map((point) => point.year);
    const values = points.map((point) => point.value);
    let minValue = Math.min(...values);
    let maxValue = Math.max(...values);
    const padding = Math.max((maxValue - minValue) * 0.15, maxValue * 0.02, 0.5);
    minValue = Math.max(options.zeroFloor ? 0 : -Infinity, minValue - padding);
    maxValue += padding;
    const minYear = Math.min(...years);
    const maxYear = Math.max(...years);
    const x = (year) => margin.left + ((year - minYear) / Math.max(maxYear - minYear, 1)) * (width - margin.left - margin.right);
    const y = (value) => margin.top + ((maxValue - value) / Math.max(maxValue - minValue, 1)) * (height - margin.top - margin.bottom);
    const svg = makeSvg(width, height);

    for (let index = 0; index <= 4; index += 1) {
      const value = minValue + ((maxValue - minValue) * index) / 4;
      const yPos = y(value);
      svg.appendChild(svgElement("line", { x1: margin.left, y1: yPos, x2: width - margin.right, y2: yPos, class: "grid-line" }));
      const label = svgElement("text", { x: margin.left - 10, y: yPos + 3, "text-anchor": "end", class: "axis-label" });
      label.textContent = formatValue(value, options.digits ?? 1);
      svg.appendChild(label);
    }

    const tickYears = [...new Set(years)].sort((left, right) => left - right);
    tickYears.forEach((year) => {
      const label = svgElement("text", { x: x(year), y: height - 13, "text-anchor": "middle", class: "axis-label" });
      label.textContent = year;
      svg.appendChild(label);
    });

    cleanSeries.forEach((item) => {
      const linePoints = item.points.map((point) => `${x(point.year)},${y(point.value)}`).join(" ");
      svg.appendChild(svgElement("polyline", { points: linePoints, class: `context-line-${item.style}` }));
      item.points.forEach((point) => {
        const circle = svgElement("circle", { cx: x(point.year), cy: y(point.value), r: 3.5, class: `context-dot-${item.style}` });
        const title = svgElement("title");
        title.textContent = `${item.label}, ${point.year}: ${formatValue(point.value, options.digits ?? 1)}`;
        circle.appendChild(title);
        svg.appendChild(circle);
      });
    });

    container.appendChild(svg);
  }

  function populateControls() {
    const country = currentCountry();
    const areaSelect = byId("area-select");
    const metricSelect = byId("metric-select");
    const previousArea = state.areaCode;
    areaSelect.replaceChildren();
    country.entities.forEach((entity) => {
      const option = document.createElement("option");
      option.value = entity.area_code;
      option.textContent = state.country === "USA" ? `${entity.area_name} | ${entity.macro_region}` : entity.area_name;
      areaSelect.appendChild(option);
    });
    state.areaCode = country.entities.some((entity) => entity.area_code === previousArea)
      ? previousArea
      : country.entities[0].area_code;
    areaSelect.value = state.areaCode;

    metricSelect.replaceChildren();
    Object.entries(country.metrics)
      .sort(([, left], [, right]) => left.label.localeCompare(right.label))
      .forEach(([key, metric]) => {
        const option = document.createElement("option");
        option.value = key;
        option.textContent = metric.label;
        metricSelect.appendChild(option);
    });
    if (!country.metrics[state.metric]) state.metric = country.default_metric;
    metricSelect.value = state.metric;
  }

  function renderRanking(entity, metric) {
    const peers = metricEntities()
      .map((item) => ({
        area_code: item.area_code,
        name: item.area_name,
        value: Number(item.metrics[state.metric].latest_value),
      }))
      .sort((left, right) => right.value - left.value);
    const rank = peers.findIndex((item) => item.area_code === entity.area_code) + 1;
    const values = peers.map((item) => item.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const peerMedian = median(values);
    const comparisonPct = peerMedian ? ((Number(metric.latest_value) - peerMedian) / peerMedian) * 100 : 0;
    byId("peer-rank").textContent = `${rank} of ${peers.length}`;
    byId("peer-comparison").textContent = `${Math.abs(comparisonPct).toFixed(1)}% ${comparisonPct >= 0 ? "above" : "below"} peer median`;
    byId("ranking-count").textContent = `${peers.length} areas`;

    const chart = byId("ranking-chart");
    chart.replaceChildren();
    const visible = peers.length > 12
      ? [...peers.slice(0, 5), ...peers.filter((item) => item.area_code === entity.area_code), ...peers.slice(-5)]
          .filter((item, index, list) => list.findIndex((candidate) => candidate.area_code === item.area_code) === index)
      : peers;
    visible.forEach((item) => {
      const row = document.createElement("div");
      row.className = `rank-row${item.area_code === entity.area_code ? " is-selected" : ""}`;
      const width = max === min ? 50 : 12 + ((item.value - min) / (max - min)) * 88;
      row.innerHTML = `
        <span class="rank-label" title="${item.name}">${item.name}</span>
        <span class="rank-track"><i style="width:${width.toFixed(1)}%"></i></span>
        <span class="rank-value">${formatValue(item.value, 1)}</span>
      `;
      chart.appendChild(row);
    });
    return peerMedian;
  }

  function renderHypotheses(metricKey, areaValue, peerMedian) {
    const templates = state.data.hypotheses[metricKey] || [];
    const list = byId("hypothesis-list");
    list.replaceChildren();
    const difference = peerMedian ? ((areaValue - peerMedian) / peerMedian) * 100 : null;
    templates.forEach((template) => {
      const article = document.createElement("article");
      article.className = "hypothesis-card";
      const why = difference === null
        ? "Peer comparison is unavailable for this selection."
        : `Observed aggregate value is ${Math.abs(difference).toFixed(1)}% ${difference >= 0 ? "above" : "below"} the country peer median.`;
      article.innerHTML = `
        <p class="why">${why}</p>
        <h3>${template.title}</h3>
        <p>${template.investigation_prompt}</p>
        <p class="guardrail">${template.interpretation_guardrail}</p>
        <a href="${template.evidence_url}" target="_blank" rel="noreferrer">Review supporting evidence</a>
      `;
      list.appendChild(article);
    });
    if (!templates.length) {
      const article = document.createElement("article");
      article.className = "hypothesis-card";
      article.innerHTML = "<h3>No hypothesis template</h3><p>This metric is shown descriptively without an automated explanation layer.</p>";
      list.appendChild(article);
    }
  }

  function renderSpending(entity) {
    const spending = entity.spending;
    const history = spending.history || [];
    byId("spending-definition").textContent = spending.measure_type || "No comparable spending series is available.";
    byId("spending-source-name").textContent = spending.source_name || "Not available";
    byId("spending-source-link").href = spending.source_url || "#";
    if (!history.length) {
      byId("spending-value").textContent = "Not available";
      byId("spending-period").textContent = "No matched series";
      drawLineChart(byId("spending-chart"), [], [], {});
      return;
    }
    const first = history[0];
    const latest = history[history.length - 1];
    const change = ((latest.spending_per_capita - first.spending_per_capita) / first.spending_per_capita) * 100;
    byId("spending-value").textContent = formatCurrency(spending.latest_value, spending.currency);
    byId("spending-period").textContent = spending.latest_period;
    byId("spending-first").textContent = `${formatCurrency(first.spending_per_capita, spending.currency)} | ${first.period}`;
    byId("spending-latest").textContent = `${formatCurrency(latest.spending_per_capita, spending.currency)} | ${latest.period}`;
    byId("spending-change").textContent = `${change >= 0 ? "+" : ""}${change.toFixed(1)}% nominal`;
    drawLineChart(byId("spending-chart"), history, [], {
      valueKey: "spending_per_capita",
      currency: spending.currency,
      zeroFloor: true,
    });
  }

  function sourceUrl(sourceId) {
    return state.data.sources.find((source) => source.id === sourceId)?.url || "#";
  }

  function renderContext(entity, metric) {
    const secondaryKey = byId("context-secondary-key");
    const contextChart = byId("context-chart");
    if (state.country === "UK") {
      const history = (entity.health_index || []).map((item) => ({
        year: item.year,
        value: item.health_index,
      }));
      byId("context-title").textContent = `Health Index: ${entity.area_name}`;
      byId("context-description").textContent = "ONS Health Index scores provide a broader regional outcome context. Higher scores indicate better measured health relative to the index framework.";
      byId("context-key-primary").textContent = entity.area_name;
      secondaryKey.hidden = true;
      byId("context-source-link").href = sourceUrl("uk_ons_index");
      byId("context-note").textContent = "England 2015 is the index reference value of 100. This context series is not a disease prevalence measure.";
      contextChart.setAttribute("aria-label", `ONS Health Index history for ${entity.area_name}`);
      drawComparisonChart(contextChart, [
        { label: entity.area_name, style: "primary", points: history },
      ], { digits: 1 });
      return;
    }

    const peers = currentCountry().entities.filter(
      (candidate) => candidate.macro_region === entity.macro_region && candidate.metrics[state.metric]
    );
    const years = [...new Set(peers.flatMap((candidate) => candidate.metrics[state.metric].history.map((item) => Number(item.year))))].sort();
    const peerHistory = years.map((year) => ({
      year,
      value: median(peers.map((candidate) => {
        const observation = candidate.metrics[state.metric].history.find((item) => Number(item.year) === year);
        return observation ? Number(observation.value) : NaN;
      })),
    })).filter((item) => Number.isFinite(item.value));
    const selectedHistory = metric.history.map((item) => ({ year: item.year, value: item.value }));
    byId("context-title").textContent = `${entity.macro_region} peer trajectory`;
    byId("context-description").textContent = `${entity.area_name} is compared with the unweighted annual median for states in the same CMS macro region.`;
    byId("context-key-primary").textContent = entity.area_name;
    byId("context-key-secondary").textContent = `${entity.macro_region} median`;
    secondaryKey.hidden = false;
    byId("context-source-link").href = metric.source_url;
    byId("context-note").textContent = "This peer context is descriptive. It does not adjust for population size, demographics or spatial dependence.";
    contextChart.setAttribute("aria-label", `${metric.label} history for ${entity.area_name} and ${entity.macro_region} median`);
    drawComparisonChart(contextChart, [
      { label: entity.area_name, style: "primary", points: selectedHistory },
      { label: `${entity.macro_region} median`, style: "secondary", points: peerHistory },
    ], { digits: 1, zeroFloor: true });
  }

  function render() {
    const country = currentCountry();
    const entity = currentEntity();
    const metric = entity.metrics[state.metric];
    const forecast = metric.forecast;
    document.querySelectorAll("[data-country]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.country === state.country));
    });
    byId("atlas-summary").textContent = `${entity.area_name} | ${metric.label} | ${metric.latest_period}`;
    byId("latest-value").textContent = `${formatValue(metric.latest_value, 1)}%`;
    byId("latest-period").textContent = `${metric.latest_period} | ${metric.measure_type}`;
    byId("trend-title").textContent = `${metric.label}: ${entity.area_name}`;
    byId("measure-type").textContent = metric.measure_type;
    byId("measure-population").textContent = metric.population;
    byId("source-name").textContent = metric.source_name;
    byId("source-link").href = metric.source_url;
    byId("coverage-note").textContent = `${country.coverage_note} Selected indicator: ${describeCoverage(metric.history)}. Spending: ${describeCoverage(entity.spending.history, "spending_per_capita")}.`;

    const peerMedian = renderRanking(entity, metric);
    if (forecast) {
      const slope = Number(forecast.slope_per_year);
      byId("trend-direction").textContent = `${slope >= 0 ? "+" : ""}${formatValue(slope, 2)} pp / year`;
      byId("model-quality").textContent = forecast.quality;
      byId("forecast-method").textContent = forecast.name;
      byId("forecast-error").textContent = forecast.backtest_smape_pct == null
        ? "Backtest unavailable"
        : `Rolling backtest sMAPE ${formatValue(forecast.backtest_smape_pct, 1)}%`;
      byId("forecast-note").textContent = `Observed history: ${describeCoverage(metric.history)}. ${forecast.quality}; the model uses the latest ${forecast.observations} observations (${forecast.training_start_year}-${forecast.training_end_year}). The band reflects residual variation, not structural uncertainty.`;
    } else {
      byId("trend-direction").textContent = "Not modelled";
      byId("model-quality").textContent = "Insufficient annual observations";
      byId("forecast-method").textContent = "No forecast produced";
      byId("forecast-error").textContent = "At least four annual observations are required";
      byId("forecast-note").textContent = `Observed history: ${describeCoverage(metric.history)}. The series is shown without extrapolation because the minimum history requirement was not met.`;
    }

    drawLineChart(byId("trend-chart"), metric.history, forecast ? forecast.points : [], { zeroFloor: true });
    renderSpending(entity);
    renderContext(entity, metric);
    renderHypotheses(state.metric, Number(metric.latest_value), peerMedian);
    byId("cross-country-warning").textContent = state.data.meta.cross_country_warning;
    byId("extract-date").textContent = `Source extract: ${state.data.meta.extract_date}`;
    byId("trend-chart").setAttribute("aria-label", `${metric.label} history and forecast for ${entity.area_name}`);
    byId("spending-chart").setAttribute("aria-label", `Health spending history for ${entity.area_name}`);
    state.atlas.setData(state.country, country.entities, state.metric, state.areaCode);
  }

  async function init() {
    try {
      const globeLoad = loadScript(GLOBE_SCRIPT_URL).catch((error) => {
        console.warn("Globe.GL could not be loaded; using the local dotted atlas fallback.", error);
      });
      const [response, geographyResponse] = await Promise.all([
        fetch(DATA_URL),
        fetch(GEOGRAPHY_URL),
      ]);
      if (!response.ok) throw new Error(`Data request failed with ${response.status}`);
      if (!geographyResponse.ok) {
        throw new Error(`Geography request failed with ${geographyResponse.status}`);
      }
      state.data = await response.json();
      const geography = await geographyResponse.json();
      await globeLoad;
      state.atlas = new RegionalAtlas(byId("atlas-globe"), geography, (country, areaCode) => {
        state.country = country;
        state.areaCode = areaCode;
        populateControls();
        render();
      });
      populateControls();
      render();

      document.querySelectorAll("[data-country]").forEach((button) => {
        button.addEventListener("click", () => {
          state.country = button.dataset.country;
          state.areaCode = null;
          populateControls();
          render();
        });
      });
      byId("area-select").addEventListener("change", (event) => {
        state.areaCode = event.target.value;
        render();
      });
      byId("metric-select").addEventListener("change", (event) => {
        state.metric = event.target.value;
        render();
      });
      const loadingState = byId("loading-state");
      loadingState.classList.add("is-hidden");
      loadingState.hidden = true;
    } catch (error) {
      byId("loading-state").textContent = "The regional dataset could not be loaded. Open this preview through a local web server.";
      console.error(error);
    }
  }

  init();
})();
