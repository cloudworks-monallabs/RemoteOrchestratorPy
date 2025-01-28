def func_with_resources(arg):
    print("resource is created")
    yield
    print("resource is destroyed")


gen = func_with_resources(5)

def init_resource_and_work(gen):
    try:
        # Start the generator to initialize the resource
        next(gen)
    except StopIteration:
        raise RuntimeError("Resource generator is already exhausted.")

    pass

def do_work(afunc, args):
    # do the work
    
    afunc(*args)

do_work(init_resource_and_work, [gen])

def teardown(afunc, args):
    # consume gen to destroy the resource
    afunc(*args)
    pass

def clean_resources(gen):
    try:
        # Finalize the generator to clean up resources
        next(gen)
    except StopIteration:
        pass



teardown(clean_resources, [gen])
