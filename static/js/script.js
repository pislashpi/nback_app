document.addEventListener('DOMContentLoaded', function() {
    let index = 0;
    let responses = [];
    let stimulusArea = document.getElementById('stimulus-area');
    let distractorArea = document.getElementById('distractor-area');
    let totalStimuli = stimuliList.length;

    function countdown(seconds) {
        if (seconds > 0) {
            stimulusArea.innerHTML = `<span style="color: black; font-size: 48px;">${seconds}</span>`;
            setTimeout(function() {
                countdown(seconds - 1);
            }, 1000);
        } else {
            stimulusArea.innerHTML = ''; // カウントダウン終了後に消去
            showStimulus();
        }
    }

    function showStimulus() {
        if (index < totalStimuli) {
            // 刺激の表示
            stimulusArea.innerHTML = stimuliList[index].value;

            // 邪魔な画像の表示
            if (distractor) {
                // プレースホルダーの邪魔な画像を表示（例として 'placeholder.png' を使用）
                distractorArea.innerHTML = `
                    <img src="/images/placeholders/placeholder.png" alt="distractor" class="distractor-image left">
                    <img src="/images/placeholders/placeholder.png" alt="distractor" class="distractor-image right">
                `;
            }

            let stimulusStartTime = Date.now();

            // 要素の表示時間
            setTimeout(function() {
                stimulusArea.innerHTML = '';
                distractorArea.innerHTML = ''; // 邪魔な画像を消去

                let stimulusEndTime = Date.now();

                // インターバル時間
                setTimeout(function() {
                    index++;
                    showStimulus();
                }, intervalTime);
            }, displayTime);
        } else {
            // タスク終了、結果を送信
            fetch('/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(responses)
            })
            .then(response => response.json())
            .then(data => {
                // 結果ページへリダイレクト
                window.location.href = '/result';
            });
        }
    }

    document.addEventListener('keydown', function(event) {
        if (event.code === 'Space') {
            responses.push({index: index, response: true});
        }
    });

    document.addEventListener('click', function() {
        responses.push({index: index, response: true});
    });

    // タスク開始前にカウントダウンを表示
    countdown(3);
});
