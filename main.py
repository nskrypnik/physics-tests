import math
from physics import phy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.uix.scatter import ScatterPlane
from kivy.graphics import Color, Rectangle, Ellipse


GRAVITY = 0, 0

Builder.load_string('''
#place kivy notation of app here
''')


class GraphicalObject(object):
    
    def __init__(self, **kw):
        self.widget = self.create_widget(**kw)
        
    def create_widget(self):
        ''' Should be implemented in subclass '''
        raise NotImplemented


class PhysicalObject(GraphicalObject):
        
    def __init__(self, world, mass, pos=(0, 0), **kw):
        ''' Create a physical object inside of the space '''
        super(PhysicalObject, self).__init__(**kw)
        self.world = world
        self.mass = mass
        self.pos = pos
        self.elasticity = kw.pop('elasticity', 0.)
        self.moment = self.get_moment()
        self.body = body = self.body_factory()     
        shapes = self.create_shapes(**kw)
        if isinstance(shapes, list):
            self.world.space.add(*shapes)
        else:
            self.world.space.add(shapes)
        body.data = self
        self.world.objects.append(self)
        self.world.add_widget(self.widget)
        
    def body_factory(self):
        body = phy.Body(self.mass, self.moment)
        body.position = self.pos
        self.world.space.add(body)
        return body

    def update(self):
        ''' Should be implemented in subclass '''
        raise NotImplemented
    
    def get_moment(self, **kw):
        ''' Should be implemented in subclass '''
        raise NotImplemented
    
    def create_shapes(self, **kw):
        ''' Should be implemented in subclass '''
        raise NotImplemented


class Box(PhysicalObject):

    def __init__(self, *args, **kw):
        self.size = kw.pop('size', (100., 100.))
        self.color = kw.pop('color', (1., 0., 0, 1))
        super(Box, self).__init__(*args, **kw)
    
    def update(self):
        p = self.body.position
        self.widget.center = (p.x, p.y)
        self.widget.rotation = math.degrees(self.body.angle)
        
    def get_moment(self, **kw):
        size = self.size
        return phy.moment_for_box(self.mass, size[0], size[1])
    
    def create_widget(self, **kw):
        widget = ScatterPlane(pos=(0, 0), size=self.size)
        with widget.canvas:
            Color(*self.color)
            Rectangle(pos=(0, 0), size=self.size)
        return widget
            
    def create_shapes(self, **kw):
        shape = phy.Poly.create_box(self.body, size=self.size)
        shape.elasticity = self.elasticity
        return shape
        

class Circle(PhysicalObject):

    def __init__(self, *args, **kw):
        self.radius = kw.pop('radius', 100.)
        self.color = kw.pop('color', (1., 0., 0, 1))
        super(Circle, self).__init__(*args, **kw)

    def update(self):
        p = self.body.position
        self.widget.center = (p.x, p.y)        

    def get_moment(self, **kw):
        return phy.moment_for_circle(self.mass, 0, self.radius, (0, 0))
    
    def create_widget(self, **kw):
        size = self.radius*2, self.radius*2
        widget = ScatterPlane(pos=(0, 0), size=size)
        with widget.canvas:
            Color(*self.color)
            Ellipse(pos=(0, 0), size=size)
        return widget
            
    def create_shapes(self, **kw):
        shape = phy.Circle(self.body, radius=self.radius)
        shape.elasticity = self.elasticity
        return shape
        
        
class StaticBox(PhysicalObject):

    def __init__(self, world, pos=(0, 0), **kw):
        self.color = kw.pop('color', (0, 0, 1, 1))
        self.size = kw.pop('size', (100., 100.))
        super(StaticBox, self).__init__(world, None, pos=pos, **kw)
        
    def get_moment(self):
        return None
        
    def create_widget(self):
        widget = Widget(size=self.size)
        with widget.canvas:
            Color(*self.color)
            Rectangle(pos=(0, 0), size=self.size)
        return widget
    
    def update(self):
        p = self.body.position
        self.widget.center = (p.x, p.y)  

    def create_shapes(self, **kw):
        size = self.size
        shape = phy.Poly.create_box(self.body, size=self.size)
        shape.elasticity = self.elasticity
        return shape
        
    def body_factory(self):
        return self.world.space.static_body


class PlayGround(Widget):
    
    bounds = ListProperty([])
    objects = ListProperty([])
    
    def __init__(self, **kw):
        super(PlayGround, self).__init__(**kw)
        self.init_physics()
        self.bind(size=self.update_bounds, pos=self.update_bounds)
        self.create_world()
        Clock.schedule_interval(self.update, 1 / 30.)
    
    def init_physics(self):
        
        self.space = space = phy.Space()
        space.iterations = 30
        space.gravity = GRAVITY
        space.sleep_time_threshold = 0.5
        space.collision_slop = 0.5
        
        self.update_bounds()
        
    def update_bounds(self, *largs):
        space = self.space
        x0, y0 = self.pos
        x1 = self.right
        y1 = self.top
        if len(self.bounds):
            a, b, c, d = self.bounds
            self.space.remove(a)
            self.space.remove(b)
            self.space.remove(c)
            self.space.remove(d)
        a = phy.Segment(space.static_body,
                    phy.Vec2d(x0, y0), phy.Vec2d(x1, y0), 10.0)
        b = phy.Segment(space.static_body,
                    phy.Vec2d(x1, y0), phy.Vec2d(x1, y1), 10.0)
        c = phy.Segment(space.static_body,
                    phy.Vec2d(x1, y1), phy.Vec2d(x0, y1), 10.0)
        d = phy.Segment(space.static_body,
                    phy.Vec2d(x0, y1), phy.Vec2d(x0, y0), 10.0)
        self.space.add(a)
        self.space.add(b)
        self.space.add(c)
        self.space.add(d)
        self.cbounds = [a, b, c, d]
    
    def update(self, dt):
        ''' Update the worlds '''
        self.space.step(1 / 30.)
        for obj in self.objects:
            obj.update()

    def on_touch_down(self, touch):
        shape = self.space.point_query_first(phy.Vec2d(touch.x, touch.y))
        print shape
    
    def create_world(self):
        Box(self, 10000., pos=(300, 400), size=(200, 100), color=(1, 1, 0, 1))
        Box(self, 10000., pos=(450, 550), size=(200, 100), color=(1, 0, 0, 1))
        Box(self, 10000., pos=(250, 500), size=(50, 100), color=(1, 0, 1, 1))
        Circle(self, 10000., pos=(100, 300), radius=30, color=(1, 0.5, 0.5, 1), elasticity=1.0)
        Circle(self, 10000., pos=(200, 500), radius=50, color=(0, 1, 0.5, 1))
        #StaticBox(self, pos=(100, 300), size=(200., 100.))

class PhysicsApp(App):
    
    def build(self):
        root = PlayGround()
        return root
        

if __name__ == '__main__':
    PhysicsApp().run()
