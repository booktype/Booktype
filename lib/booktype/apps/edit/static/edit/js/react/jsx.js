define(function () {
  'use strict';

  var buildMap = {};

  var getSourceMapConfig = function (config) {
    var fallback = config.isBuild ? false : 'inline';

    if (config && config.babel && 'sourceMaps' in config.babel) {
      return config.babel.sourceMaps;
    } else {
      return fallback;
    }
  };

  var ensureJSXFileExtension = function (name, config) {
    var fileExtension = config && config.jsx && config.jsx.fileExtension || '.jsx';

    if (name.indexOf(fileExtension) === -1) {
      name = name + fileExtension;
    }

    return name;
  };

  var jsx = {
    load: function (name, parentRequire, onLoadNative, config) {
      name = ensureJSXFileExtension(name, config);

      parentRequire([
          'tools/babel-standalone.min',
          'tools/require.text'
        ],
        function (babel, text) {
          text.load(name, parentRequire, function (content) {

            try {
              // TODO: this below should be extendable in config
              var babelOptions = {
                sourceFileName: config.baseUrl + name,
                sourceMaps: getSourceMapConfig(config),
                filename: config.baseUrl + name,
                presets: ['react'],
                plugins: [
                  'transform-class-properties',
                  'transform-object-rest-spread',
                  'transform-flow-strip-types'
                ],
              };
              var result = babel.transform(content, babelOptions);

              onLoadNative.fromText(result.code);
            } catch (err) {
              onLoadNative.error(err);
            }
          });
        }
      );
    },

    write: function (pluginName, name, write) {
      if (typeof buildMap[name] === 'string') {
        var text = buildMap[name];

        write.asModule(pluginName + '!' + name, text);
      } else {
        throw new Error('Module not found in build map: ' + name);
      }
    }
  };

  return jsx;
});