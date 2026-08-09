// Demo snapshot matching Open Hardware Monitor's real /data.json shape:
// GenerateJSON (Utilities/HttpServer.cs) emits preformatted display strings,
// not numbers — "52.0 °C", "1,234 RPM" — and a pre-order integer id.
// This mirrors that exactly so the parser is exercised the same way
// a live machine would exercise it. window.OHM_DEMO() returns a fresh
// tree with slightly jittered values on every call, so polling demo
// data animates like a live feed.
(function () {
  'use strict';

  let id = 0;
  const jitter = (base, spread) => base + (Math.random() - 0.5) * 2 * spread;

  const sensor = (name, fmt, base, spread, min, max) => {
    const v = jitter(base, spread);
    return {
      id: ++id, Text: name, Children: [],
      Min: fmt(min), Value: fmt(v), Max: fmt(max),
      ImageURL: 'images/transparent.png'
    };
  };

  const group = (name, icon, children) => ({
    id: ++id, Text: name, Children: children,
    Min: '', Value: '', Max: '', ImageURL: 'images_icon/' + icon + '.png'
  });

  const degC = v => v.toFixed(1) + ' °C';
  const pct = v => Math.max(0, Math.min(100, v)).toFixed(1) + ' %';
  const mhz = v => v.toFixed(1) + ' MHz';
  const rpm = v => Math.round(v).toLocaleString('en-US') + ' RPM';
  const watt = v => v.toFixed(1) + ' W';
  const volt = v => v.toFixed(3) + ' V';
  const gb = v => v.toFixed(1) + ' GB';

  window.OHM_DEMO = function () {
    id = 0;
    const root = { id: id++, Text: 'Sensor', Children: [], Min: 'Min', Value: 'Value', Max: 'Max', ImageURL: '' };

    const machine = group('FORGE-01', 'computer', []);

    machine.Children.push(group('ASUS ROG STRIX B550-F', 'mainboard', [
      group('Nuvoton NCT6798D', 'chip', [
        group('Voltages', 'voltage', [
          sensor('CPU VCore', volt, 1.26, 0.03, 0.9, 1.45),
          sensor('+3.3V', volt, 3.31, 0.01, 3.28, 3.34),
          sensor('+12V', volt, 12.10, 0.05, 11.98, 12.19)
        ]),
        group('Temperatures', 'temperature', [
          sensor('System', degC, 38, 1.5, 33, 44),
          sensor('VRM', degC, 52, 3, 41, 68)
        ]),
        group('Fans', 'fan', [
          sensor('Chassis #1', rpm, 820, 40, 650, 1210),
          sensor('Chassis #2', rpm, 760, 40, 620, 1150)
        ])
      ])
    ]));

    machine.Children.push(group('AMD Ryzen 9 5950X', 'cpu', [
      group('Clocks', 'clock', [
        sensor('Bus Speed', mhz, 99.8, 0.1, 99.6, 100.0),
        sensor('Core #1', mhz, 4650, 250, 2200, 5030),
        sensor('Core #2', mhz, 4480, 250, 2200, 5030),
        sensor('Core #3', mhz, 3720, 400, 2200, 4900),
        sensor('Core #4', mhz, 3650, 400, 2200, 4900)
      ]),
      group('Temperatures', 'temperature', [
        sensor('Core (Tctl/Tdie)', degC, 63, 6, 38, 84),
        sensor('CCD1', degC, 58, 5, 36, 79),
        sensor('CCD2', degC, 56, 5, 35, 77)
      ]),
      group('Load', 'load', [
        sensor('CPU Total', pct, 42, 18, 2, 100),
        sensor('CPU Core #1', pct, 65, 25, 1, 100),
        sensor('CPU Core #2', pct, 48, 25, 1, 100)
      ]),
      group('Powers', 'power', [
        sensor('CPU Package', watt, 88, 20, 21, 142),
        sensor('CPU Cores', watt, 71, 18, 12, 121)
      ])
    ]));

    machine.Children.push(group('Generic Memory', 'ram', [
      group('Load', 'load', [ sensor('Memory', pct, 54, 3, 31, 78) ]),
      group('Data', 'hdd', [
        sensor('Used Memory', gb, 17.2, 0.8, 9.8, 24.9),
        sensor('Available Memory', gb, 14.6, 0.8, 7.0, 22.1)
      ])
    ]));

    machine.Children.push(group('NVIDIA GeForce RTX 3080', 'nvidia', [
      group('Clocks', 'clock', [
        sensor('GPU Core', mhz, 1740, 120, 210, 1995),
        sensor('GPU Memory', mhz, 9251, 0, 405, 9251)
      ]),
      group('Temperatures', 'temperature', [ sensor('GPU Core', degC, 71, 5, 34, 83) ]),
      group('Load', 'load', [
        sensor('GPU Core', pct, 76, 20, 0, 100),
        sensor('GPU Memory', pct, 61, 10, 4, 88)
      ]),
      group('Fans', 'fan', [ sensor('GPU', rpm, 1650, 150, 0, 2820) ]),
      group('Powers', 'power', [ sensor('GPU Power', watt, 248, 40, 18, 334) ])
    ]));

    machine.Children.push(group('Samsung SSD 980 PRO 1TB', 'hdd', [
      group('Temperatures', 'temperature', [ sensor('Temperature', degC, 44, 2, 31, 56) ]),
      group('Load', 'load', [ sensor('Used Space', pct, 67.4, 0, 67.4, 67.4) ])
    ]));

    root.Children.push(machine);
    return root;
  };
})();
