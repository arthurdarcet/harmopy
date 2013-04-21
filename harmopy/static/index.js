var STATUS_REFRESH = 3000;
var store = {
    status: {},
    history: null,
    config: {},
    files: {},
};

var templates = {};
var history_fetched = false;

load = function(id) {
    // Load the json into the template and append it to the elem
    $.get('/' + id, function(data){
        $('#' + id + ' .data').html('');
        if(id == 'history'){
            store.history = data;
            return draw_history();
        }
        $.each([].concat(data), function(i, elem) {
            store[id][elem.id] = elem;
            if (elem.id == 'DEFAULT')
                return;
            var html = templates[id](elem);
            $('#' + id + ' .loading').hide();
            $('#' + id + ' .data').append(html);
            $('#' + id + ' .showondata').removeClass('hidden');
        });
        if(id == 'files')
            on_file_load(data);
        if(id == 'status' && store.history){
            store.history.push({
                time: data['time'],
                speed: data['speed'] || 0,
            });
        }
    });
};

on_file_load = function(data) {
    if(!data[0].editable) {
        $('#edit-defaults').addClass('hidden');
        return;
    }

    $('#edit-defaults').removeClass('hidden');
    $('.do-file-edit').click(function() {
        var data = store.files[$(this).data('id')];
        var html = templates.file_edit(data);
        $('#file-edit .data').html(html);
        $('#file-edit').hide();
        $('#file-edit').removeClass('hidden');
        $('#file-edit').fadeIn();
    });
    $('.confirm').click(function() {
        $(this).button('loading');
        $('#modal #confirmed').data('id', $(this).data('id'));
        $('#modal #confirmed').data('action', $(this).data('action'));
        $('#modal #modal-message').html($(this).data('confirm-message'));
        $('#modal').modal('show');
    });
};

Handlebars.registerHelper('file_config', function(title, name, file) {
    var placeholder = store.files['DEFAULT'][name];
    if(name == 'id')
        placeholder = '';
    return new Handlebars.SafeString(templates.file_config({
        'name': name,
        'title': title,
        'placeholder': placeholder,
        'value': (file && (file.id == 'DEFAULT' || file[name] != placeholder)) ? file[name] : '',
    }));
});

function draw_history() {
    var line = [];
    for(var i=0; i<store.history.length; i++)
        line.push([
            new Date(store.history[i].time*1000),
            store.history[i].speed
        ]);
    $('#history .loading').hide();
    $('#history .data').removeClass('hidden');
    $('#history .data').html('');
    $.jqplot('history .data', [line], {
        gridPadding: {right: 35},
        axes: {
            xaxis: {
                renderer: $.jqplot.DateAxisRenderer,
                tickOptions: {formatString: '%H:%M:%S'},
            },
            yaxis: {
                min: 0,
                pad: 1.1,
            }
        },

        grid: {
            drawGridLines: true,        // wether to draw lines across the grid or not.
            gridLineColor: '#cccccc',    // *Color of the grid lines.
            background: '#fcfcfc',      // CSS color spec for background color of grid.
            borderColor: '#eee',     // CSS color spec for border around grid.
            borderWidth: 0.5,           // pixel width of border around grid.
            shadow: false,               // draw a shadow for grid.
            renderer: $.jqplot.CanvasGridRenderer,  // renderer to use to draw the grid.
            rendererOptions: {}         // options to pass to the renderer.  Note, the default
                                        // CanvasGridRenderer takes no additional options.
        },

        seriesDefaults: {
            color: '#afa',      // CSS color spec to use for the line.  Determined automatically.
            lineWidth: 2.5, // Width of the line in pixels.
            shadow: false,   // show shadow or not.
            showMarker: false,   // render the data point markers or not.
            fill: true,        // fill under the line,
            fillAndStroke: true,       // *stroke a line at top of fill area.
            fillColor: '#afa',       // *custom fill color for filled lines (default is line color).
            fillAlpha: 0.3,       // *custom alpha to apply to fillColor.
        },
    });
    setTimeout(draw_history, STATUS_REFRESH);
}

$(document).ready(function() {
    templates = {
        status: Handlebars.compile($('#status-template').html()),
        config: Handlebars.compile($('#config-template').html()),
        files: Handlebars.compile($('#files-template').html()),
        file_edit: Handlebars.compile($('#file_edit-template').html()),
        file_config: Handlebars.compile($('#file_config-template').html()),
    }

    refresh = function(){
        load('status');
        setTimeout(refresh, STATUS_REFRESH);
    }

    refresh();
    load('history');
    load('config');
    load('files');

    $('.alert .close').click(function(){
        $('.alert').fadeOut();
    });
    $('#confirmed').click(function(){
        $('#modal').modal('hide');
        var action = $(this).data('action');
        $('#file-' + $(this).data('id') + ' .file-' + action).button('loading');
        $.get('/' + action + '/' + $(this).data('id'), function(data) {
            $('.confirm').button('reset');
            if (data.status != 200) {
                $('.alert #error-msg').html(data.error);
                $('.alert').hide();
                $('.alert').removeClass('hidden');
                $('.alert').fadeIn();
                setTimeout(function(){
                    $('.alert').fadeOut();
                }, 10000);
            } else {
                if(action == 'delete')
                    $('#file-' + data.id).fadeOut();
                else if(action == 'expand'){
                    $.each(data.files, function(i, file) {
                        $(templates.files(file).trim()).insertAfter('#file-' + data.id);
                    });
                    $('#file-'+data.id).fadeOut();
                }
            }
        })
    });
    $('#modal').on('hide', function(){
        $('.confirm').button('reset');
        $('.confirm').button('reset');
    });
    $('#modal').on('show', function(){
        $('#modal').removeClass('hidden');
    });
});
