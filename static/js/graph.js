$(function () {
 $("#chart").shieldChart({
 theme: "light",
 seriesSettings: {
 line: {
 dataPointText: {
 enabled: true
 }
 }
 },
 chartLegend: {
 align: 'center',
 borderRadius: 2,
 borderWidth: 2,
 verticalAlign: 'top'
 },
 exportOptions: {
 image: true,
 print: true
 },
 axisX: {
  categoricalValues: ['2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']
 },
 axisY: {
 title: {
 text: "Цена (₽ за kWh)"
 }
 },
 primaryHeader: {
 text: "Цены на электроэнергию"
 },
 dataSeries: [{
 seriesType: 'line',
 collectionAlias: 'Потребители, корме населения РФ',
  data: [2.4, 2.6, 2.8, 3, 3.2, 3.3, 3.5, 3.7]
 }, {
 seriesType: 'line',
 collectionAlias: 'Население РФ',
 data: [2.7, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4]
 }]
 });
 });