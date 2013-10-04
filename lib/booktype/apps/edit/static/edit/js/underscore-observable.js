   function Observable( $locks ){

      var topics = {};

      this.on = function( topic, callback, scope ){
        if ( typeof callback === 'function' ) {
          var observers = topics[topic] = topics[topic] || [],
          observer = [callback, scope];

          observers.push(observer);
          return [ topic, observers.indexOf(observer) ];
        } else {
          return false;
        }
      };

      this.emit = function( topic ){

        var observers = topics[topic],
        args = _.toArray(arguments).slice(1);

        if (observers) {

          _.each(observers, function (value) {
           try {
            if (value) {
              value[0].apply(value[1] || null, args);
            }
          } catch (err) { }
        });
          return true;
        } else {
          return false;
        }
      };

      this.off = function( handle ){
        var topic = handle[0], idx = handle[1];
        if (topics[topic] && topics[topic][idx]) {
            // delete value so the indexes don't move
            delete topics[topic][idx];
            // If the topic is only set with falsy values, delete it;
            if (!topics[topic].some(function (value) {
              return !!value;
            })) {
              delete topics[topic];
            }
            return true;
          } else {
            return false;
          }
        };
    }


