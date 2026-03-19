<?php
use Illuminate\Support\Facades\Route;
use Illuminate\Http\Request;

$questions = [
    ['id' => 1, 'authorId' => 101, 'title' => 'Як працює REST?', 'body' => 'Поясніть принцип REST API'],
    ['id' => 2, 'authorId' => 101, 'title' => 'Лабораторну здав успішно?', 'body' => 'Скажіть оцінку']
];

$answers = [
    ['id' => 1, 'questionId' => 1, 'authorId' => 202, 'body' => 'REST базується на HTTP методах'],
    ['id' => 2, 'questionId' => 2, 'authorId' => 202, 'body' => 'Максимальний бал']
];

Route::get('/questions', function () use ($questions) {
    return response()->json($questions);
});

Route::post('/questions', function (Request $request) use ($questions) {
    $newQuestion = [
        'id' => count($questions) + 1,
        'authorId' => $request->input('authorId'),
        'title' => $request->input('title'),
        'body' => $request->input('body'),
    ];

    return response()->json($newQuestion, 201);
});

Route::get('/questions/{id}/answers', function ($id) use ($answers) {
    $filtered = array_filter($answers, function ($answer) use ($id) {
        return $answer['questionId'] == $id;
    });

    return response()->json(array_values($filtered));
});
