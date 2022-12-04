import random
import time


class Lift:
    def __init__(self):
        self.NUM_FLOORS = 11  # 0 - 10
        self.direction = 0  # 0 -> no direction, 1 -> up, 2 -> down
        self.current_pos = 0
        self.destination = 0
        self.buttons_pressed = [False] * self.NUM_FLOORS
        self.floor_requests = [0] * self.NUM_FLOORS
        self.up_timestamp = [None] * self.NUM_FLOORS
        self.down_timestamp = [None] * self.NUM_FLOORS
        self.exit = False
        # 0 -> no request
        # 1 -> up
        # 2 -> down
        # 3 -> both

        self.lift_movement()

    def scan_request(self):
        # produce a random floor request with random direction
        random_button = random.choice([0, 1, 2, 3])
        random_floor = random.randint(0, self.NUM_FLOORS - 1)

        if random_floor == 0:
            random_button = 1
        if random_floor == self.NUM_FLOORS - 1:
            random_button = 2
        if random_button != 0:
            # if there is already a request, ensure the new request doesn't nullify prev request
            if self.floor_requests[random_floor] == 0:
                self.floor_requests[random_floor] = random_button
            elif self.floor_requests[random_floor] == 1 and random_button >= 2:
                self.floor_requests[random_floor] = 3
            elif self.floor_requests[random_floor] == 2 and (random_button == 1 or random_button == 3):
                self.floor_requests[random_floor] = 3

        print(f"Random floor: {random_floor} and Random button: {random_button}")

    def lift_movement(self):
        # moves the lift, produce new scan_request
        while not self.exit:
            self.scan_request()
            self.find_destination_on_floor_requests()
            if self.floor_requests.count(0) == self.NUM_FLOORS and self.buttons_pressed.count(True) == 0:
                self.direction = 0

            if self.direction == 0 and self.floor_requests.count(0) != self.NUM_FLOORS:
                # if lift is not moving, and is present at the floor request
                self.button_request()
                self.floor_requests[self.current_pos] = 0
                self.find_destination_on_button_requests()
                print(f"Passenger picked up at floor: {self.current_pos} for destination: {self.destination}")

            if self.direction:
                self.move_lift()

            if self.direction:
                if self.buttons_pressed[self.current_pos]:  # Passenger dropped based on button request
                    self.buttons_pressed[self.current_pos] = False
                    print(f"Passenger Dropped at floor: {self.current_pos}")

                if self.current_pos != self.destination:
                    # not at destination, but floor request at current floor
                    if (self.direction == 1 and (
                            self.floor_requests[self.current_pos] == 1 or self.floor_requests[self.current_pos] == 3)):
                        self.floor_requests[self.current_pos] -= self.direction
                        self.button_request()  # it should allow only up direction button request
                        print(f"Passenger picked up at floor: {self.current_pos} for destination: {self.destination}")

                    if (self.direction == 2 and (
                            self.floor_requests[self.current_pos] == 2 or self.floor_requests[self.current_pos] == 3)):
                        self.floor_requests[self.current_pos] -= self.direction
                        self.button_request()  # it should allow only down direction button request
                        print(f"Passenger picked up at floor: {self.current_pos} for destination: {self.destination}")

                elif self.current_pos == self.destination:
                    # we are at the destination and we need to find the next destination based floor
                    # max button request is made the next destination and direction
                    if self.direction:
                        self.button_request()
                        if self.floor_requests[self.current_pos] == 3:
                            self.floor_requests[self.current_pos] -= self.direction
                        else:
                            self.floor_requests[self.current_pos] = 0
                    self.find_destination_on_button_requests()
                    print(f"Passenger picked up at floor: {self.current_pos} for destination: {self.destination}")

    def button_request(self):
        if self.current_pos == self.destination:  # the lift has reached the destination on floor request
            # passenger is generating button request according to floor request
            if self.floor_requests[self.current_pos] == 3:
                if self.direction == 0:
                    self.direction = random.randint(1, 3)

                if self.direction == 1:
                    random_floor = random.randint(self.current_pos + 1, self.NUM_FLOORS - 1)
                elif self.direction == 2:
                    random_floor = random.randint(0, self.current_pos - 1)

                self.buttons_pressed[random_floor] = True
                print(f"button_pressed: {random_floor}")
                return
            elif self.floor_requests[self.current_pos] == 1:
                random_floor = random.randint(self.current_pos + 1, self.NUM_FLOORS - 1)
                self.direction = 1
            else:
                random_floor = random.randint(0, self.current_pos - 1)
                self.direction = 2
            self.buttons_pressed[random_floor] = True
            print(f"button_pressed: {random_floor}")
            return
        # on the way to destination
        if self.direction == 1:
            random_floor = random.randint(self.current_pos + 1, self.NUM_FLOORS - 1)
        else:
            random_floor = random.randint(0, self.current_pos - 1)
        self.buttons_pressed[random_floor] = True
        print(f"button_pressed: {random_floor}")

    def find_destination_on_floor_requests(self):
        # reroute destination according to new floor requests
        if self.floor_requests.count(0) == self.NUM_FLOORS:
            return
        floor_requests_index_list = []  # floor_requests_index_list contains all the floors where buttons are pressed (not 0)
        for index in range(self.NUM_FLOORS):
            if self.floor_requests[index] != 0:
                floor_requests_index_list.append(index)

        if self.direction == 0:  # life is stationary
            distance_from_current = {abs(self.current_pos - x): x for x in floor_requests_index_list}
            # floor request is on same floor where lift is stationed
            # chooses the destination as the farthest floor request from current position
            if distance_from_current[(max(distance_from_current.keys()))] == self.current_pos:
                self.direction = 0
                self.destination = self.current_pos
            elif distance_from_current[(max(distance_from_current.keys()))] > self.current_pos:
                self.direction = 1
                self.destination = distance_from_current[(max(distance_from_current.keys()))]
            else:
                self.direction = 2
                self.destination = self.current_pos - max(distance_from_current.keys())


        else:
            # chooses the destination as the farthest floor request from current position
            flr_requests = {}
            for index in range(self.NUM_FLOORS):
                if self.floor_requests[index] != 0:
                    flr_requests[index] = self.floor_requests[index]
            if len(flr_requests.keys()) != 0:
                if self.direction == 1 and max(flr_requests.keys()) > self.destination:
                    self.destination = max(flr_requests.keys())
                elif self.direction == 2 and min(flr_requests.keys()) < self.destination:
                    self.destination = min(flr_requests.keys())
            print(f"Floor requests for direction {self.direction}: {flr_requests}")

    def move_lift(self):
        # moves the lift
        if self.current_pos == 0 or self.current_pos == self.NUM_FLOORS - 1:
            if self.current_pos == 0:
                if self.floor_requests.count(0) == self.NUM_FLOORS and self.buttons_pressed.count(True) == 0:
                    self.direction = 0
                else:
                    self.direction = 1
                    self.current_pos += 1
            else:
                if self.floor_requests.count(0) == self.NUM_FLOORS and self.buttons_pressed.count(True) == 0:
                    self.direction = 0
                else:
                    self.direction = 2
                    self.current_pos -= 1
        else:
            if self.direction == 1:
                self.current_pos += 1
            elif self.direction == 2:
                self.current_pos -= 1
        print(f"Moving lift Direction: {self.direction} and Current_Position: {self.current_pos}")
        button_pressed_index_list = [] # list of the floors pressed in the lift
        for index in range(self.NUM_FLOORS):
            if self.buttons_pressed[index] == True:
                button_pressed_index_list.append(index)
        print(f"Drop off locations: {button_pressed_index_list}")
        time.sleep(2)

    def find_destination_on_button_requests(self):
        # reroute destination according to new button requests
        button_pressed_index_list = [] # list with all the floors pressed in the lift
        for index in range(self.NUM_FLOORS):
            if self.buttons_pressed[index] == True:
                button_pressed_index_list.append(index)
        # based on the current stationary position of the lift nd the floor request received it should determine the
        # destination
        if self.direction == 0:
            distance_from_current = {abs(self.current_pos - x): x
                                     for x in self.buttons_pressed_index_list}
            if distance_from_current[(max(distance_from_current.keys()))] > self.current_pos:
                self.direction = 1
                self.destination = distance_from_current[(max(distance_from_current.keys()))]
            else:
                self.direction = 2
                self.destination = self.current_pos - max(distance_from_current.keys())

        elif self.direction == 1 and self.current_pos != self.destination:
            max_button_request = [self.buttons_pressed.index(x) for x in self.buttons_pressed if x is not False]
            requests = [] + max_button_request
            if len(requests) != 0:
                if max(requests) > self.destination:
                    self.destination = max(requests)
        elif self.direction == 2 and self.current_pos != self.destination:
            min_button_request = [self.buttons_pressed.index(x) for x in self.buttons_pressed if x != False]
            requests = [] + min_button_request
            if len(requests) != 0:
                if min(requests) < self.destination:
                    self.destination = min(requests)


class Floor:
    def __init__(self, floor_number):
        self.floor_number = floor_number

    def raise_request(self):
        while not lift.exit:
            waiting_time = random.randint(10, 15)
            time.sleep(waiting_time)
            print(f"Sending the request for floor_number {self.floor_number}\n")
            lift.scan_request(self.floor_number)


lift = Lift()

