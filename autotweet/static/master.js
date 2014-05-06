$(function() {
    $(window).on('submit', function(event){
        var target = $(event.target);

        if (target.hasClass('query')) {
            query(target);
        } else if (target.hasClass('teach')) {
            teach(target);
        }
        event.preventDefault();
    });

    function query(target) {
        var payload = target.serialize();
        var input = target.find('[name=query]');
        var query = input.val();
        var p = $('<p>');
        var span = $('<span>');
        var messages = $('#messages');

        span.text(query);
        span.addClass('msg');
        p.addClass('message');
        p.addClass('me');
        p.append(span)
        messages.append(p);

        input.val(null);

        $.ajax(target.attr('action'), {
            method: target.attr('method'),
            data: payload,
            success: function(data) {
                var p = $('<p>');
                var span = $('<span>');
                var answer = $('<span>');
                var ratio = $('<span>');
                answer.text(data.answer);
                answer.addClass('content');
                ratio.text(data.ratio);
                ratio.addClass('ratio');
                span.addClass('msg');
                span.append(answer);
                span.append(ratio);
                p.addClass('message');
                p.addClass('other');
                p.append(span);
                messages.append(p);
                messages.scrollTop(messages[0].scrollHeight);
            },
            error: function() {
                var data = 'I cannot answer. please teach me.';
                var p = $('<p>');
                var span = $('<span>');
                span.text(data);
                span.addClass('msg');
                p.addClass('message');
                p.addClass('other');
                p.append(span);
                messages.append(p);
                messages.scrollTop(messages[0].scrollHeight);
            }
        });

        messages.scrollTop(messages[0].scrollHeight);
    }

    function teach(target) {
        var payload = target.serialize();

        $.ajax(target.attr('action'), {
            method: target.attr('method'),
            data: payload,
            success: function() {
                target[0].reset();
            },
        });
    }

    $('input[type=text]').focus();
});
