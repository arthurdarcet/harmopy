var STATUS_REFRESH = 3000;
var store = {
    status: {},
    logs: {},
    history: null,
    config: {},
    files: {},
};

var templates = {};
var history_fetched = false;

load = function(id, hide_before) {
    // Load the json into the template and append it to the elem
    if(hide_before) {
        $('#' + id + ' .data').hide();
        $('#' + id + ' .showondata').addClass('hidden');
        $('#' + id + ' .loading').show();
    }
    $('#' + id).show();
    $.get('/' + id, function(data){
        $('#' + id + ' .data').html('');
        $('#' + id + ' .data').show();
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
        if(id == 'config')
            post_config('#config', 'config');
        if(id == 'logs') {
            var elems = $('.logs .data').children();
            while(elems.length > 100)
                $(elems[elems.length - 1]).remove();
        }
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
        var data = store.files[$(this).data('id')] || {};
        var html = templates.file_edit(data);
        $('#file-edit .data').html(html);
        post_config('#file-edit', 'files');
        $('#file-edit .close').click(function(){
            $('#file-edit').hide();
        });
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

post_config = function(form, url) {
    $(form + ' .data .submit').click(function(){
        var button = $(this);
        button.button('loading');
        var data = {config_key: button.data('id')};
        $.each($(form + '-' + button.data('id') + ' input'), function(){
            data[this.name] = this.value;
        });
        $.post('/' + url, data, function(ret) {
            show_result(ret);
            $(form).hide();
            load(url, true);
        });
        return false;
    });
}

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
                pad: 1,
            },
            yaxis: {
                min: 0,
                pad: 1.03,
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

var alert_timeout = null;
function show_result(ret) {
    clearTimeout(alert_timeout);
    $('.alert').hide();
    $('.alert').removeClass('hidden');
    $('.alert').removeClass('alert-error');
    $('.alert').removeClass('alert-success');
    if(ret.status == 200) {
        $('.alert').addClass('alert-success');
        $('.alert #msg').html('Config saved');
        $('.alert #error').hide();
        $('.alert #success').show();
    } else {
        $('.alert').addClass('alert-error');
        $('.alert #msg').html(ret.error);
        $('.alert #success').hide();
        $('.alert #error').show();
    }
    $('.alert').fadeIn();
    alert_timeout = setTimeout(function(){
        $('.alert').fadeOut();
    }, 10000);
}

$(document).ready(function() {
    templates = {
        status: Handlebars.compile($('#status-template').html()),
        logs: Handlebars.compile($('#logs-template').html()),
        config: Handlebars.compile($('#config-template').html()),
        files: Handlebars.compile($('#files-template').html()),
        file_edit: Handlebars.compile($('#file_edit-template').html()),
        file_config: Handlebars.compile($('#file_config-template').html()),
    }

    refresh = function(){
        load('status');
        load('logs');
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
            show_result(data);
            if (data.status == 200) {
                load('files');
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
