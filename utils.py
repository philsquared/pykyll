import os

def fatalError( msg ):
    print("\n\n** {}\n\n".format( msg ) )
    raise Exception( msg )

def ensureDirs( dir ):
    if not os.path.exists(dir):
    	os.makedirs(dir)
def ensureParentDirs( dir ):
	ensureDirs(os.path.dirname(dir))
