var countdown =  $("#countdown").countdown360({
    radius      : 90,
    seconds     : 20,
    strokeWidth : 15,
    fillStyle   : '#D32F2F',
    strokeStyle : '#F44336',
    fontSize    : 50,
    fontColor   : '#FFF',
    label: ['sec', 'secs'],
    autostart: false,
    onComplete  : function () {
        $("#countdown").css('display','none');
        $("#upload_bar").css('display','block');
        $('.button[data-active=true]').click();
        console.log('completed')
    }
});

$('.button[data-active=false]').on('click',function(event) {
    var recording = true;
    console.log('recording : '+recording);
    $(this).css('display','none');
    // $(this).next().css('display','block');
    startRecording(this);
    $("#countdown").css('display','block');
    countdown.start();
});

$('.button[data-active=true]').on('click',function(event) {
    var recording = false;
    console.log('recording : '+recording);
    $(this).css('display','none');
    $(this).prev().css('display','block');
    stopRecording(this);
});

window.onload = function init() {
    try {
      // webkit shim
      window.AudioContext = window.AudioContext || window.webkitAudioContext;
      navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia;
      window.URL = window.URL || window.webkitURL;

      audio_context = new AudioContext;
      __log('Audio context set up.');
      __log('navigator.getUserMedia ' + (navigator.getUserMedia ? 'available.' : 'not present!'));
    } catch (e) {
      alert('No web audio support in this browser!');
    }

    navigator.getUserMedia({audio: true}, startUserMedia, function(e) {
      __log('No live audio input: ' + e);
    });
};

function __log(e, data) {
    log.innerHTML += "<br>" + e + " " + (data || '');
}

var audio_context;
var recorder;

function startUserMedia(stream) {
    var input = audio_context.createMediaStreamSource(stream);
    __log('Media stream created.');

    // Uncomment if you want the audio to feedback directly
    //input.connect(audio_context.destination);
    //__log('Input connected to audio context destination.');

    recorder = new Recorder(input);
    __log('Recorder initialised.');
}

function startRecording(button) {
    recorder && recorder.record();
    button.disabled = true;
    button.nextElementSibling.disabled = false;
    __log('Recording...');
}

function stopRecording(button) {
    recorder && recorder.stop();
    button.disabled = true;
    button.previousElementSibling.disabled = false;
    __log('Stopped recording.');

    // create WAV download link using audio data blob
    // createDownloadLink();

    search_sample();

    recorder.clear();
}

function createDownloadLink() {
    recorder && recorder.exportWAV(function(blob) {
      var url = URL.createObjectURL(blob);
      var li = document.createElement('li');
      var au = document.createElement('audio');
      var hf = document.createElement('a');

      au.controls = true;
      au.src = url;
      hf.href = url;
      hf.download = new Date().toISOString() + '.wav';
      hf.innerHTML = hf.download;
      li.appendChild(au);
      li.appendChild(hf);
      recordingslist.appendChild(li);
    });
}

function showNoResultDialog() {
    var dialog2 = new BootstrapDialog({
        message: function(dialogRef){
                var $message = $('<div><h3>Results:</h3>' +
                    '<h2 class="center-block" style="text-align: center;">No Results found! :( </h2><br/></div>');

                var $button = $('<button class="btn btn-info" style="background-color: #2E4E58;">Thanks!</button>');
                $button.on('click', {dialogRef: dialogRef}, function(event){
                    event.data.dialogRef.close();
                });
                $message.append($button);

                return $message;
            },
            closable: false
        });

    dialog2.realize();
    dialog2.getModalHeader().hide();
    dialog2.getModalFooter().hide();
    dialog2.getModalBody().css('background', '#4B606B url("/static/img/icon_black.png") no-repeat right top');
    dialog2.getModalBody().css('color', '#fff');
    dialog2.open();
}


function search_sample(){
    recorder && recorder.exportWAV(function(blob) {
        var xhttp = new XMLHttpRequest();
        xhttp.onload = function(e) {
            $("#upload_bar").css('display','none');
            if (this.status == 200) {
                var data = JSON.parse(xhttp.responseText);
                console.log(xhttp.responseText);
                if(data.successful == true){
                    var song_name = data.song_name;
                    var related_song_array = data.related;
                    var time = data.search_time;

                    var dialog = new BootstrapDialog({
                    message: function(dialogRef){
                            var message = '<div><h3>Results:</h3>' +
                                'Search Completed in ' + time + '. Top result is:' +
                                '<h2 class="center-block" style="text-align: center;">' + song_name +
                                '<h2/><br/><h3>Related Songs:</h3><ul style="padding: 15px;">';
                            for (var i = 0; i < related_song_array.length; i++) {
                                message += '<li>' + related_song_array[i].song_name + '</li>';
                            }
                            message += '</ul></div>';
                            var $button = $('<button class="btn btn-info" style="background-color: #2E4E58;">Thanks!</button>');
                            $button.on('click', {dialogRef: dialogRef}, function(event){
                                event.data.dialogRef.close();
                            });
                        return $(message).append($button);
                        },
                        closable: false
                    });

                    dialog.realize();
                    dialog.getModalHeader().hide();
                    dialog.getModalFooter().hide();
                    dialog.getModalBody().css('background', '#4B606B url("/static/img/icon_black.png") no-repeat right top');
                    dialog.getModalBody().css('color', '#fff');
                    dialog.open();
                }else{
                    showNoResultDialog();
                }
                // console.log(this.responseText);
            }else{
                showNoResultDialog();
            }
        };

        xhttp.open("POST", "/search", true);

        // Listen to the upload progress.
        var progressBar = document.querySelector('progress');
        xhttp.upload.onprogress = function(e) {
            if (e.lengthComputable) {
              progressBar.value = (e.loaded / e.total) * 100;
              progressBar.textContent = progressBar.value; // Fallback for unsupported browsers.
            }
        };

        var file = new File([blob], "sample.wav");

        var fd = new FormData();
        fd.append("file", file);

        xhttp.send(fd);
    });
}