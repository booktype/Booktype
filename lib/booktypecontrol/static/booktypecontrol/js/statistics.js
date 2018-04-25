(function (win, $) {
  'use strict';

  win.booktype.statistics = {
    init: function () {

      var usersChartData = JSON.parse($('#users-stats').attr('data-chart'));

      // users stats
      new Chart(document.getElementById("users-stats"), {
        type: 'line',
        data: {
          labels: usersChartData.users_increasing.labels,
          datasets: [
            {
              label: 'Users increasing',
              data: usersChartData.users_increasing.data,
              backgroundColor: [
                'rgba(173, 31, 26, 0.1)'
              ],
              borderColor: [
                'rgba(173, 31, 26, 1)'
              ],
              borderWidth: 1
            },
            {
              label: 'Sign ups',
              data: usersChartData.signups.data,
              backgroundColor: [
                'rgba(52, 161, 28, 0.5)'
              ],
              borderColor: [
                'rgba(52, 161, 28, 1)'
              ],
              borderWidth: 1
            }
          ]
        }
      });

      // active users
      new Chart(document.getElementById("last-year-login"), {
        type: 'doughnut',
        data: {
          labels: usersChartData.last_year_login.labels,
          datasets: [
            {
              label: "Users",
              backgroundColor: ["green", "lightgrey"],
              data: usersChartData.last_year_login.data
            }
          ]
        },
        options: {
          title: {
            display: true,
            text: 'Users who logged in during last year'
          }
        }
      });
      new Chart(document.getElementById("last-month-login"), {
        type: 'doughnut',
        data: {
          labels: usersChartData.last_month_login.labels,
          datasets: [
            {
              label: "Users",
              backgroundColor: ["green", "lightgrey"],
              data: usersChartData.last_month_login.data
            }
          ]
        },
        options: {
          title: {
            display: true,
            text: 'Users who logged in last 30 days'
          }
        }
      });

      // books
      new Chart(document.getElementById("books-count"), {
        type: 'line',
        data: {
          labels: usersChartData.books_per_year.labels,
          datasets: [
            {
              label: 'Books created per year',
              data: usersChartData.books_increasing_per_year.data,
              backgroundColor: [
                'rgba(173, 31, 26, 0.1)'
              ],
              borderColor: [
                'rgba(173, 31, 26, 1)'
              ],
              borderWidth: 1
            },
            {
              label: 'Books per year',
              data: usersChartData.books_per_year.data,
              backgroundColor: [
                'rgba(52, 161, 28, 0.5)'
              ],
              borderColor: [
                'rgba(52, 161, 28, 1)'
              ],
              borderWidth: 1
            }
          ]
        }
      });

      new Chart(document.getElementById("last-year-notlogin-avrg-books"), {
        type: 'bar',
        data: {
          labels: usersChartData.not_active_users_books_count.labels,
          datasets: [
            {
              label: "Users",
              backgroundColor: ["yellow", "green", "red", "blue", "pink", "lightgreen", "aqua", "black", "brown", "chocolate"],
              data: usersChartData.not_active_users_books_count.data
            }
          ]
        },
        options: {
          legend: {display: false},
          title: {
            display: true,
            text: 'Count of users who own different amount of books. Users in the chart were not logged in during last year.'
          }
        }
      });

      new Chart(document.getElementById("last-year-login-avrg-books"), {
        type: 'bar',
        data: {
          labels: usersChartData.active_users_books_count.labels,
          datasets: [
            {
              label: "Users",
              backgroundColor: ["yellow", "green", "red", "blue", "pink", "lightgreen", "aqua", "black", "brown", "chocolate"],
              data: usersChartData.active_users_books_count.data
            }
          ]
        },
        options: {
          legend: {display: false},
          title: {
            display: true,
            text: 'Count of users who own different amount of books. Users in the chart were logged in during last year.'
          }
        }
      });

      // exports
      new Chart(document.getElementById("exports-per-year"), {
        type: 'bar',
        data: {
          labels: usersChartData.exports_per_year.labels,
          datasets: [
            {
              label: "Exports",
              backgroundColor: ["yellow", "green", "red", "blue", "pink", "lightgreen", "aqua", "black", "brown", "chocolate"],
              data: usersChartData.exports_per_year.data
            }
          ]
        },
        options: {
          legend: {display: false},
          title: {
            display: true,
            text: 'Exports per year'
          }
        }
      });

      new Chart(document.getElementById("exports-per-format"), {
        type: 'pie',
        data: {
          labels: usersChartData.exports_per_format.labels,
          datasets: [{
            label: "Population (millions)",
            backgroundColor: ["yellow", "green", "red", "blue", "pink", "lightgreen", "aqua", "black", "brown", "chocolate", "orange"],
            data: usersChartData.exports_per_format.data
          }]
        },
        options: {
          title: {
            display: true,
            text: 'Exports per format'
          }
        }
      });

    }
  };

  $(function () {
    win.booktype.statistics.init();
  });

})(window, jQuery);