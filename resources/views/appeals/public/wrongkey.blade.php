@extends('layouts.app')

@section('title', htmlspecialchars(__('appeals.wrong-key.title')))
@section('content')
    <h1>
        {{ __('appeals.wrong-key.title') }}
    </h1>

    <p>
        {{ __('appeals.wrong-key.text') }}
    </p>

    <div class="card-deck">
        <div class="card">
            <div class="card-body">
                {{ __('auth.auth-needed-screen.key-text') }}

                {{ Form::open(['url' => route('public.appeal.view'), 'method' => 'GET']) }}
                <div class="input-group w-100 mb-3">
                    {{ Form::text('hash', null, ['class' => 'form-control w-100','placeholder' => __('auth.auth-needed-screen.key-placeholder')]) }}
                </div>

                <div>
                    <button type="submit" class="btn btn-primary">{{ __('auth.auth-needed-screen.submit-text') }}</button>
                    {{-- <a href="#" class="btn btn-danger">Forgot Appeal Key</a> --}}
                </div>
                {{ Form::close() }}
            </div>
        </div>
    </div>
@endsection
