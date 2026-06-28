2026-06-28 06:29:40.796 [error] Exception in ASGI application

Traceback (most recent call last):
  File "/var/task/_vendor/vercel_runtime/_vendor/uvicorn/protocols/http/h11_impl.py", line 410, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/vercel_runtime/_vendor/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/vercel_runtime/vc_init.py", line 696, in __call__
    await self.app(new_scope, receive, send_wrapper)
  File "/var/task/_vendor/fastapi/applications.py", line 1163, in __call__
    await super().__call__(scope, receive, send)
  File "/var/task/_vendor/starlette/applications.py", line 90, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/var/task/_vendor/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/var/task/_vendor/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/var/task/_vendor/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/api/index.py", line 23, in dispatch
    resp = await call_next(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/var/task/_vendor/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/var/task/_vendor/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/var/task/_vendor/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/var/task/_vendor/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/var/task/_vendor/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/var/task/_vendor/starlette/routing.py", line 660, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/var/task/_vendor/fastapi/routing.py", line 2531, in app
    await route.handle(scope, receive, send)
  File "/var/task/_vendor/fastapi/routing.py", line 1241, in handle
    await super().handle(scope, receive, send)
  File "/var/task/_vendor/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/var/task/_vendor/fastapi/routing.py", line 150, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/var/task/_vendor/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/var/task/_vendor/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/var/task/_vendor/fastapi/routing.py", line 136, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/fastapi/routing.py", line 690, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/fastapi/routing.py", line 346, in run_endpoint_function
    return await run_in_threadpool(dependant.call, **values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/starlette/concurrency.py", line 34, in run_in_threadpool
    return await anyio.to_thread.run_sync(func)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/anyio/to_thread.py", line 63, in run_sync
    return await get_async_backend().run_sync_in_worker_thread(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/anyio/_backends/_asyncio.py", line 2596, in run_sync_in_worker_thread
    return await future
           ^^^^^^^^^^^^
  File "/var/task/_vendor/anyio/_backends/_asyncio.py", line 1029, in run
    result = context.run(func, *args)
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/api/index.py", line 116, in index
    return templates.TemplateResponse("landing.html", {"request": request})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/starlette/templating.py", line 148, in TemplateResponse
    template = self.get_template(name)
               ^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/starlette/templating.py", line 115, in get_template
    return self.env.get_template(name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/jinja2/environment.py", line 1010, in get_template
    return self._load_template(name, globals)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/jinja2/environment.py", line 958, in _load_template
    template = self.cache.get(cache_key)
               ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/jinja2/utils.py", line 466, in get
    return self[key]
           ~~~~^^^^^
  File "/var/task/_vendor/jinja2/utils.py", line 504, in __getitem__
    rv = self._mapping[key]
         ~~~~~~~~~~~~~^^^^^
TypeError: unhashable type: 'dict'
